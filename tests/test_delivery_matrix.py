import json

from cli_support import PLANNER_ID, WORKER_ID
from transport_support import TransportTestCase


class DeliveryMatrixTests(TransportTestCase):
    def test_codex_to_claude_preserves_unicode_text_and_reply_address(self) -> None:
        self.join("planner")
        listener, _ = self.claude_panel(WORKER_ID, "worker")
        message = "Xin chào Claude\nĐã kiểm tra: ✓"
        receipt = self.succeeded(self.command("send", "--to", "worker", "--message", message))
        frame = self.receive_frame(listener)
        self.assertEqual(frame["type"], "user")
        self.assertEqual(frame["session_id"], WORKER_ID)
        self.assertTrue(frame["message"]["content"].endswith(message))
        metadata = self.metadata(frame["message"]["content"])
        self.assertEqual(metadata["reply_to"], f"codex:{PLANNER_ID}")
        self.assertEqual(metadata["role"], "planner")
        self.assertEqual(receipt["status"], "submitted")
        self.assertNotIn("acknowledged", receipt)

    def test_claude_to_claude_routes_to_the_worker_socket(self) -> None:
        _, source_environment = self.claude_panel(PLANNER_ID, "planner")
        listener, _ = self.claude_panel(WORKER_ID, "worker")
        receipt = self.succeeded(
            self.command(
                "send",
                "--to",
                "worker",
                "--message",
                "review",
                provider="claude",
                overrides=source_environment,
            )
        )
        frame = self.receive_frame(listener)
        self.assertEqual(frame["session_id"], WORKER_ID)
        self.assertEqual(receipt["sender"], f"claude:{PLANNER_ID}")
        self.assertEqual(
            self.metadata(frame["message"]["content"])["reply_to"], f"claude:{PLANNER_ID}"
        )

    def test_claude_to_codex_uses_destination_profile_and_safe_arguments(self) -> None:
        capture = self.queue_executable()
        _, source_environment = self.claude_panel(PLANNER_ID, "planner")
        destination_profile = str((self.root / "destination-codex").resolve())
        self.succeeded(
            self.command(
                "join",
                "--team",
                "demo",
                "--role",
                "worker",
                session_id=WORKER_ID,
                overrides={"CODEX_HOME": destination_profile},
            )
        )
        sentinel = self.root / "unexpected-shell-command"
        message = f"Keep literal: $(touch {sentinel}); 'quote' `command`\nnext"
        receipt = self.succeeded(
            self.command(
                "send",
                "--to",
                "worker",
                "--message",
                message,
                provider="claude",
                overrides=source_environment,
            )
        )
        record = json.loads(capture.read_text())
        self.assertEqual(record["args"][:3], ["queue", "--thread", WORKER_ID])
        self.assertEqual(record["codex_home"], destination_profile)
        self.assertTrue(record["args"][4].endswith(message))
        self.assertFalse(sentinel.exists())
        self.assertEqual(receipt["status"], "queued")

    def test_codex_to_codex_can_reply_to_a_canonical_address(self) -> None:
        capture = self.queue_executable()
        self.join("planner")
        self.join("worker", WORKER_ID)
        reply_id = "44444444-4444-4444-8444-444444444444"
        receipt = self.succeeded(
            self.command(
                "send",
                "--to",
                f"codex:{PLANNER_ID}",
                "--message",
                "Tests passed",
                "--in-reply-to",
                reply_id,
                session_id=WORKER_ID,
            )
        )
        record = json.loads(capture.read_text())
        self.assertEqual(record["args"][2], PLANNER_ID)
        metadata = self.metadata(record["args"][4])
        self.assertEqual(metadata["in_reply_to"], reply_id)
        self.assertEqual(metadata["role"], "worker")
        self.assertEqual(metadata["reply_to"], f"codex:{WORKER_ID}")
        self.assertEqual(receipt["recipient"], f"codex:{PLANNER_ID}")
