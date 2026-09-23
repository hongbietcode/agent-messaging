import argparse
import json
import os
import sys
from pathlib import Path

from agent_messaging.identity import resolve_identity
from agent_messaging.messaging import send_message
from agent_messaging.models import MessagingError
from agent_messaging.registry import Registry


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Message Claude/Codex panels by team role or session address."
    )
    root.add_argument("--provider", choices=("claude", "codex"))
    root.add_argument(
        "--state-dir",
        type=Path,
        default=Path(
            os.environ.get(
                "AGENT_MESSAGING_STATE_DIR", str(Path.home() / ".local/state/agent-messaging")
            )
        ),
    )
    commands = root.add_subparsers(dest="command", required=True)
    join = commands.add_parser("join", help="Assign this panel to one team role.")
    join.add_argument("--team", required=True)
    join.add_argument("--role", choices=("planner", "worker"), required=True)
    join.add_argument("--name", default="")
    join.add_argument("--replace", action="store_true")
    listing = commands.add_parser(
        "list", help="List registered panels, not live-presence guarantees."
    )
    listing.add_argument("--team")
    commands.add_parser("whoami", help="Show this panel's registration.")
    commands.add_parser("leave", help="Remove only this panel's registration.")
    send = commands.add_parser(
        "send", help="Send a peer message; transport acceptance is not an ACK."
    )
    send.add_argument("--to", required=True)
    send.add_argument("--message", required=True)
    send.add_argument("--in-reply-to")
    return root


def execute(arguments: argparse.Namespace) -> dict[str, object]:
    registry = Registry(arguments.state_dir)
    if arguments.command == "list":
        return {"peers": [peer.to_dict() for peer in registry.list(arguments.team)]}
    identity = resolve_identity(arguments.provider or "", os.environ)
    if arguments.command == "join":
        return registry.join(
            identity, arguments.team, arguments.role, arguments.name, arguments.replace
        ).to_dict()
    if arguments.command == "whoami":
        return registry.get(identity.address).to_dict()
    if arguments.command == "leave":
        return {"address": identity.address, "left": registry.leave(identity.address)}
    if arguments.command == "send":
        return send_message(
            registry, identity, arguments.to, arguments.message, arguments.in_reply_to
        )
    raise MessagingError("Unknown command.")


def main() -> int:
    arguments = parser().parse_args()
    try:
        result = execute(arguments)
    except (MessagingError, OSError) as error:
        sys.stderr.write(json.dumps({"error": str(error)}, ensure_ascii=False) + "\n")
        return 1
    sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    return 0
