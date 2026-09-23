import json
import os
import socket
import stat
from pathlib import Path

from agent_messaging.models import MessagingError, Peer


def validate_destination(recipient: Peer) -> None:
    record_path = Path(recipient.native_registry_file)
    record_stat = record_path.lstat()
    if not stat.S_ISREG(record_stat.st_mode) or record_stat.st_uid != os.getuid():
        raise MessagingError("Claude session registry is not a regular file owned by this user.")
    try:
        record = json.loads(record_path.read_text())
    except ValueError as error:
        raise MessagingError("Cannot read the Claude session registry.") from error
    if (
        not isinstance(record, dict)
        or record.get("sessionId") != recipient.session_id
        or record.get("messagingSocketPath") != recipient.socket_path
    ):
        raise MessagingError("Claude session identity or inbox changed; rejoin that panel.")
    metadata = Path(recipient.socket_path).lstat()
    if not stat.S_ISSOCK(metadata.st_mode) or metadata.st_uid != os.getuid():
        raise MessagingError("Claude destination must be a socket owned by this user.")


def deliver_claude(recipient: Peer, sender: Peer, message_id: str, content: str) -> str:
    validate_destination(recipient)
    frame = {
        "type": "user",
        "from": sender.address,
        "session_id": recipient.session_id,
        "uuid": message_id,
        "msg_id": message_id,
        "priority": "next",
        "message": {"role": "user", "content": content},
    }
    encoded = (json.dumps(frame, ensure_ascii=False) + "\n").encode("utf-8")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(5)
        try:
            connection.connect(recipient.socket_path)
        except OSError as error:
            raise MessagingError(
                f"Cannot connect to Claude inbox; nothing sent: {error}"
            ) from error
        try:
            connection.sendall(encoded)
            connection.shutdown(socket.SHUT_WR)
        except OSError as error:
            raise MessagingError(
                "Claude delivery is uncertain; check the receiver before retrying."
            ) from error
    return "submitted"
