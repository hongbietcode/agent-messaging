import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = PLUGIN_ROOT / "skills" / "agent-messaging" / "scripts" / "run.py"
PLANNER_ID = "11111111-1111-4111-8111-111111111111"
WORKER_ID = "22222222-2222-4222-8222-222222222222"
OTHER_ID = "33333333-3333-4333-8333-333333333333"


class CommandTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="am-", dir="/tmp")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.state = self.root / "state"
        self.environment = os.environ.copy()
        for name in ("CODEX_THREAD_ID", "CODEX_SESSION_ID", "CLAUDE_CODE_MESSAGING_SOCKET"):
            self.environment.pop(name, None)
        self.environment["CODEX_HOME"] = str(self.root / "codex")
        self.environment["CLAUDE_CONFIG_DIR"] = str(self.root / "claude")
        self.environment["PYTHONDONTWRITEBYTECODE"] = "1"

    def command(
        self,
        *arguments: str,
        provider: str = "codex",
        session_id: str = PLANNER_ID,
        overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = self.environment | {"CODEX_THREAD_ID": session_id}
        environment.update(overrides or {})
        return subprocess.run(
            [
                sys.executable,
                str(ENTRYPOINT),
                "--state-dir",
                str(self.state),
                "--provider",
                provider,
                *arguments,
            ],
            env=environment,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )

    def succeeded(self, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def failed(self, result: subprocess.CompletedProcess[str]) -> str:
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        self.assertTrue(result.stderr.lstrip().startswith("{"), result.stderr)
        return str(json.loads(result.stderr)["error"])

    def join(self, role: str, session_id: str = PLANNER_ID) -> dict[str, object]:
        return self.succeeded(
            self.command("join", "--team", "demo", "--role", role, session_id=session_id)
        )
