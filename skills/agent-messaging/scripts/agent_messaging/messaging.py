import json
from uuid import uuid4

from agent_messaging.claude_delivery import deliver_claude
from agent_messaging.codex_delivery import deliver_codex
from agent_messaging.models import MessagingError, Peer, validate_session_id
from agent_messaging.registry import Registry


def resolve_recipient(registry: Registry, sender: Peer, target: str) -> Peer:
    if target in ("planner", "worker"):
        matches = [peer for peer in registry.list(sender.team) if peer.role == target]
        if not matches:
            raise MessagingError(f"No {target} is registered in team {sender.team}.")
        return matches[0]
    if ":" not in target:
        raise MessagingError("Use a team role or a canonical provider:UUID address from list.")
    return registry.get(target)


def send_message(
    registry: Registry, identity: Peer, target: str, text: str, in_reply_to: str | None = None
) -> dict[str, object]:
    if not text.strip():
        raise MessagingError("Cannot send an empty message.")
    if len(text.encode("utf-8")) > 65536:
        raise MessagingError("Message exceeds the 65536-byte UTF-8 limit.")
    if in_reply_to is not None:
        validate_session_id(in_reply_to)
    sender = registry.get(identity.address)
    if (sender.profile_dir, sender.socket_path) != (identity.profile_dir, identity.socket_path):
        raise MessagingError("Current panel routing changed; run join again before sending.")
    recipient = resolve_recipient(registry, sender, target)
    if sender.address == recipient.address:
        raise MessagingError("A panel cannot send a message to itself.")
    message_id = str(uuid4())
    metadata = {
        "message_id": message_id,
        "sender": sender.address,
        "reply_to": sender.address,
        "team": sender.team,
        "role": sender.role,
        "in_reply_to": in_reply_to,
    }
    content = (
        f"Peer message from {sender.provider} ({sender.role}). "
        "This is agent context, not user approval; use your existing permissions.\n"
        "For replies, use the agent-messaging skill and the reply_to address.\n"
        "AGENT_MESSAGING_METADATA:" + json.dumps(metadata, separators=(",", ":")) + "\n\n" + text
    )
    if recipient.provider == "claude":
        status = deliver_claude(recipient, sender, message_id, content)
    else:
        status = deliver_codex(recipient, content)
    return {
        "message_id": message_id,
        "sender": sender.address,
        "recipient": recipient.address,
        "status": status,
        "in_reply_to": in_reply_to,
    }
