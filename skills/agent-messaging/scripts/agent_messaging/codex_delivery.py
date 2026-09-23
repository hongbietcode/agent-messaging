import os
import subprocess

from agent_messaging.models import MessagingError, Peer


def deliver_codex(recipient: Peer, content: str) -> str:
    environment = os.environ.copy()
    environment["CODEX_HOME"] = recipient.profile_dir
    try:
        result = subprocess.run(
            ["codex", "queue", "--thread", recipient.session_id, "--message", content],
            cwd=recipient.cwd,
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise MessagingError("Codex queue timed out; check delivery before retrying.") from error
    except OSError as error:
        raise MessagingError(f"Cannot run Codex queue: {error}") from error
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise MessagingError(f"Codex queue failed ({result.returncode}): {detail[:2000]}")
    return "queued"
