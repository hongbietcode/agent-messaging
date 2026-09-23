import json

from cli_support import PLANNER_ID, WORKER_ID
from transport_support import TransportTestCase


class DeliveryErrorTests(TransportTestCase):
    def test_changed_sender_profile_requires_rejoining_before_sending(self) -> None:
        capture = self.queue_executable()
        self.join("planner")
        self.join("worker", WORKER_ID)
        result = self.command(
            "send",
            "--to",
            "worker",
            "--message",
            "x",
            overrides={"CODEX_HOME": str(self.root / "other-profile")},
        )
        self.assertIn("join", self.failed(result))
        self.assertFalse(capture.exists())

    def test_empty_message_never_calls_the_queue(self) -> None:
        capture = self.queue_executable()
        self.join("planner")
        self.join("worker", WORKER_ID)
        self.assertIn(
            "empty", self.failed(self.command("send", "--to", "worker", "--message", " "))
        )
        self.assertFalse(capture.exists())

    def test_self_send_is_refused(self) -> None:
        self.join("planner")
        self.assertIn(
            "itself", self.failed(self.command("send", "--to", "planner", "--message", "x"))
        )

    def test_missing_role_never_guesses_a_destination(self) -> None:
        self.join("planner")
        self.assertIn(
            "worker", self.failed(self.command("send", "--to", "worker", "--message", "x"))
        )

    def test_queue_failure_is_reported_and_never_retried(self) -> None:
        capture = self.queue_executable()
        self.join("planner")
        self.join("worker", WORKER_ID)
        result = self.command(
            "send", "--to", "worker", "--message", "test", overrides={"AM_TEST_FAIL": "1"}
        )
        self.assertIn("queue", self.failed(result))
        self.assertEqual(len(capture.read_text().splitlines()), 1)

    def test_stale_claude_session_record_is_not_used(self) -> None:
        self.join("planner")
        listener, _ = self.claude_panel(WORKER_ID, "worker")
        record_path = self.root / "claude" / "sessions" / f"{WORKER_ID}.json"
        record = json.loads(record_path.read_text())
        record["sessionId"] = PLANNER_ID
        record_path.write_text(json.dumps(record))
        self.assertIn(
            "changed", self.failed(self.command("send", "--to", "worker", "--message", "x"))
        )
        listener.setblocking(False)
        with self.assertRaises(BlockingIOError):
            listener.accept()

    def test_symlinked_claude_socket_is_rejected(self) -> None:
        self.join("planner")
        listener, _ = self.claude_panel(WORKER_ID, "worker")
        socket_path = self.root / f"{WORKER_ID[:8]}.sock"
        moved_path = self.root / "moved.sock"
        socket_path.rename(moved_path)
        socket_path.symlink_to(moved_path)
        self.assertIn(
            "socket", self.failed(self.command("send", "--to", "worker", "--message", "x"))
        )
        listener.setblocking(False)
        with self.assertRaises(BlockingIOError):
            listener.accept()

    def test_missing_claude_socket_does_not_report_success(self) -> None:
        self.join("planner")
        listener, _ = self.claude_panel(WORKER_ID, "worker")
        listener.close()
        (self.root / f"{WORKER_ID[:8]}.sock").unlink()
        result = self.command("send", "--to", "worker", "--message", "x")
        self.failed(result)
        self.assertEqual(result.stdout, "")

    def test_oversized_message_is_refused_before_queue_invocation(self) -> None:
        capture = self.queue_executable()
        self.join("planner")
        self.join("worker", WORKER_ID)
        result = self.command("send", "--to", "worker", "--message", "x" * 65537)
        self.assertIn("65536", self.failed(result))
        self.assertFalse(capture.exists())

    def test_invalid_reply_identifier_is_not_sent(self) -> None:
        capture = self.queue_executable()
        self.join("planner")
        self.join("worker", WORKER_ID)
        result = self.command(
            "send", "--to", "worker", "--message", "x", "--in-reply-to", "not-a-message-id"
        )
        self.assertIn("UUID", self.failed(result))
        self.assertFalse(capture.exists())
