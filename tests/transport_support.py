import json
import socket
import sys
from pathlib import Path

from cli_support import CommandTestCase


class TransportTestCase(CommandTestCase):
    def claude_panel(self, identity: str, role: str) -> tuple[socket.socket, dict[str, str]]:
        socket_path = self.root / f"{identity[:8]}.sock"
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(listener.close)
        listener.bind(str(socket_path))
        listener.listen(2)
        listener.settimeout(2)
        records = self.root / "claude" / "sessions"
        records.mkdir(parents=True, exist_ok=True)
        (records / f"{identity}.json").write_text(
            json.dumps(
                {
                    "sessionId": identity,
                    "name": role,
                    "messagingSocketPath": str(socket_path),
                    "kind": "interactive",
                    "version": "2.1.280",
                }
            )
        )
        overrides = {"CLAUDE_CODE_MESSAGING_SOCKET": str(socket_path)}
        self.succeeded(
            self.command(
                "join", "--team", "demo", "--role", role, provider="claude", overrides=overrides
            )
        )
        return listener, overrides

    def queue_executable(self) -> Path:
        binaries = self.root / "bin"
        binaries.mkdir()
        capture = self.root / "queued.jsonl"
        executable = binaries / "codex"
        executable.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "with Path(os.environ['AM_TEST_CAPTURE']).open('a') as target:\n"
            "    target.write(json.dumps({'args': sys.argv[1:], 'codex_home': "
            "os.environ.get('CODEX_HOME')}) + '\\n')\n"
            "sys.stderr.write('simulated queue refusal' "
            "if os.environ.get('AM_TEST_FAIL') else '')\n"
            "raise SystemExit(9 if os.environ.get('AM_TEST_FAIL') else 0)\n"
        )
        executable.chmod(0o700)
        self.environment["PATH"] = f"{binaries}:{self.environment.get('PATH', '')}"
        self.environment["AM_TEST_CAPTURE"] = str(capture)
        return capture

    def receive_frame(self, listener: socket.socket) -> dict[str, object]:
        connection, _ = listener.accept()
        with connection:
            connection.settimeout(2)
            data = b""
            while True:
                chunk = connection.recv(65536)
                if not chunk:
                    break
                data += chunk
        self.assertEqual(len(data.splitlines()), 1)
        return json.loads(data)

    def metadata(self, content: str) -> dict[str, object]:
        line = next(
            line for line in content.splitlines() if line.startswith("AGENT_MESSAGING_METADATA:")
        )
        return json.loads(line.removeprefix("AGENT_MESSAGING_METADATA:"))
