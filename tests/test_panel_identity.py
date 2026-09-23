from cli_support import PLANNER_ID, WORKER_ID, CommandTestCase


class PanelIdentityTests(CommandTestCase):
    def test_conflicting_codex_identifiers_fail_instead_of_guessing(self) -> None:
        result = self.command(
            "join", "--team", "demo", "--role", "planner", overrides={"CODEX_SESSION_ID": WORKER_ID}
        )
        self.assertIn("conflict", self.failed(result))

    def test_missing_codex_identity_explains_which_session_metadata_is_needed(self) -> None:
        result = self.command("join", "--team", "demo", "--role", "planner", session_id="")
        self.assertIn("CODEX_THREAD_ID", self.failed(result))

    def test_malformed_session_identifier_is_rejected(self) -> None:
        result = self.command(
            "join", "--team", "demo", "--role", "planner", session_id="../../outside"
        )
        self.assertIn("UUID", self.failed(result))

    def test_claude_provider_never_falls_back_to_an_inherited_codex_identity(self) -> None:
        result = self.command(
            "join", "--team", "demo", "--role", "worker", provider="claude", session_id=PLANNER_ID
        )
        self.assertIn("CLAUDE_CODE_MESSAGING_SOCKET", self.failed(result))

    def test_unregistered_session_is_not_given_another_panels_role(self) -> None:
        self.join("planner")
        result = self.command("whoami", session_id=WORKER_ID)
        self.assertIn("join", self.failed(result))

    def test_invalid_team_name_is_rejected(self) -> None:
        result = self.command("join", "--team", " ", "--role", "planner")
        self.assertIn("team", self.failed(result))
