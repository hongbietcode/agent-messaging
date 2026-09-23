import json
import subprocess
import sys

from cli_support import ENTRYPOINT, OTHER_ID, PLANNER_ID, WORKER_ID, CommandTestCase


class PanelRoleTests(CommandTestCase):
    def test_join_persists_the_panel_identity_team_and_role(self) -> None:
        result = self.join("planner")
        self.assertEqual(result["address"], f"codex:{PLANNER_ID}")
        self.assertEqual(result["team"], "demo")
        self.assertEqual(result["role"], "planner")
        current = self.succeeded(self.command("whoami"))
        self.assertEqual(current["role"], "planner")

    def test_team_can_have_one_planner_and_one_worker(self) -> None:
        self.join("planner")
        self.join("worker", WORKER_ID)
        result = self.succeeded(self.command("list", "--team", "demo"))
        self.assertEqual({peer["role"] for peer in result["peers"]}, {"planner", "worker"})

    def test_occupied_role_is_not_silently_reassigned(self) -> None:
        self.join("planner")
        error = self.failed(
            self.command("join", "--team", "demo", "--role", "planner", session_id=OTHER_ID)
        )
        self.assertIn("occupied", error)
        current = self.succeeded(self.command("whoami"))
        self.assertEqual(current["address"], f"codex:{PLANNER_ID}")

    def test_explicit_replacement_removes_the_previous_role_holder(self) -> None:
        self.join("planner")
        self.succeeded(
            self.command(
                "join", "--team", "demo", "--role", "planner", "--replace", session_id=OTHER_ID
            )
        )
        result = self.succeeded(self.command("list"))
        self.assertEqual([peer["address"] for peer in result["peers"]], [f"codex:{OTHER_ID}"])

    def test_rejoining_the_same_panel_is_idempotent(self) -> None:
        self.join("planner")
        self.join("planner")
        result = self.succeeded(self.command("list"))
        self.assertEqual(len(result["peers"]), 1)

    def test_leave_removes_only_the_current_panel(self) -> None:
        self.join("planner")
        self.join("worker", WORKER_ID)
        self.succeeded(self.command("leave"))
        result = self.succeeded(self.command("list"))
        self.assertEqual([peer["address"] for peer in result["peers"]], [f"codex:{WORKER_ID}"])

    def test_concurrent_claims_allocate_the_role_to_only_one_panel(self) -> None:
        arguments = [
            sys.executable,
            str(ENTRYPOINT),
            "--state-dir",
            str(self.state),
            "--provider",
            "codex",
            "join",
            "--team",
            "demo",
            "--role",
            "planner",
        ]
        processes = [
            subprocess.Popen(
                arguments,
                env=self.environment | {"CODEX_THREAD_ID": identity},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for identity in (PLANNER_ID, WORKER_ID, OTHER_ID)
        ]
        for process in processes:
            process.communicate(timeout=10)
        self.assertEqual(sorted(process.returncode for process in processes), [0, 1, 1])
        result = self.succeeded(self.command("list"))
        self.assertEqual(len(result["peers"]), 1)

    def test_corrupt_registry_is_reported_without_overwriting_it(self) -> None:
        self.join("planner")
        registry = self.state / "registry.json"
        registry.write_text("broken data")
        self.assertIn("registry", self.failed(self.command("list")))
        self.assertEqual(registry.read_text(), "broken data")

    def test_state_directory_is_private(self) -> None:
        self.join("planner")
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o700)

    def test_unknown_registry_version_is_rejected(self) -> None:
        self.join("planner")
        registry = self.state / "registry.json"
        registry.write_text(json.dumps({"schema_version": 99, "peers": []}))
        self.assertIn("version", self.failed(self.command("list")))
