import json
import os
from collections.abc import Mapping
from pathlib import Path

from agent_messaging.models import MessagingError, Peer, validate_session_id


def resolve_identity(provider: str, environment: Mapping[str, str]) -> Peer:
    if provider == "codex":
        return codex_identity(environment)
    if provider == "claude":
        return claude_identity(environment)
    raise MessagingError("Choose --provider claude or --provider codex.")


def codex_identity(environment: Mapping[str, str]) -> Peer:
    thread_id = environment.get("CODEX_THREAD_ID", "")
    session_id = environment.get("CODEX_SESSION_ID", "")
    if thread_id and session_id and thread_id != session_id:
        raise MessagingError("CODEX_THREAD_ID and CODEX_SESSION_ID conflict.")
    identity = thread_id or session_id
    if not identity:
        raise MessagingError("Run inside Codex with CODEX_THREAD_ID or CODEX_SESSION_ID.")
    profile = Path(environment.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    return Peer("codex", validate_session_id(identity), str(profile.resolve()), os.getcwd())


def claude_identity(environment: Mapping[str, str]) -> Peer:
    socket_path = environment.get("CLAUDE_CODE_MESSAGING_SOCKET", "")
    if not socket_path:
        raise MessagingError("Run inside Claude with CLAUDE_CODE_MESSAGING_SOCKET available.")
    profile = Path(environment.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    socket_path = os.path.abspath(socket_path.removeprefix("uds:"))
    matches: list[Peer] = []
    for path in sorted((profile / "sessions").glob("*.json")):
        if path.is_symlink():
            continue
        try:
            record = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(record, dict) or record.get("messagingSocketPath") != socket_path:
            continue
        identity = record.get("sessionId")
        if not isinstance(identity, str):
            continue
        name = record.get("name", "")
        matches.append(
            Peer(
                "claude",
                validate_session_id(identity),
                str(profile.resolve()),
                os.getcwd(),
                socket_path=socket_path,
                native_registry_file=str(path.resolve()),
                name=name if isinstance(name, str) else "",
            )
        )
    if len(matches) != 1:
        raise MessagingError(
            "Cannot uniquely match the current Claude inbox to its session registry."
        )
    return matches[0]
