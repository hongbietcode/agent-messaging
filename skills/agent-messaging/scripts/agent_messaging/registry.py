import fcntl
import json
import os
import re
import stat
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

from agent_messaging.models import MessagingError, Peer


class Registry:
    def __init__(self, directory: Path) -> None:
        self.directory = directory.expanduser()
        self.path = self.directory / "registry.json"

    @contextmanager
    def locked(self) -> Iterator[None]:
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        metadata = self.directory.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid():
            raise MessagingError("The registry directory must be owned by the current user.")
        if metadata.st_mode & 0o077:
            raise MessagingError("The registry directory must be private (mode 0700).")
        descriptor = os.open(
            self.directory / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(descriptor, "a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def read(self) -> list[Peer]:
        if self.path.is_symlink():
            raise MessagingError("Refusing a symlinked registry.")
        if not self.path.exists():
            return []
        try:
            document = json.loads(self.path.read_text())
        except (OSError, ValueError) as error:
            raise MessagingError(f"Cannot read registry: {error}") from error
        if not isinstance(document, dict) or document.get("schema_version") != 1:
            raise MessagingError("Unsupported registry schema version.")
        values = document.get("peers")
        if not isinstance(values, list):
            raise MessagingError("Invalid registry peers.")
        peers = [Peer.from_dict(value) for value in values]
        addresses = [peer.address for peer in peers]
        roles = [(peer.team, peer.role) for peer in peers]
        if len(set(addresses)) != len(peers) or len(set(roles)) != len(peers):
            raise MessagingError("Duplicate identities or team roles in registry.")
        return peers

    def write(self, peers: list[Peer]) -> None:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", dir=self.directory, delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(
                    {"schema_version": 1, "peers": [peer.to_dict() for peer in peers]}, temporary
                )
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def list(self, team: str | None = None) -> list[Peer]:
        with self.locked():
            return sorted(
                [peer for peer in self.read() if team is None or peer.team == team],
                key=lambda peer: (peer.team, peer.role, peer.address),
            )

    def get(self, address: str) -> Peer:
        for peer in self.list():
            if peer.address == address:
                return peer
        raise MessagingError(f"Session {address} is not registered; run join in that panel.")

    def join(
        self, identity: Peer, team: str, role: str, name: str, replace_existing: bool = False
    ) -> Peer:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", team):
            raise MessagingError("Use a team name of 1–64 letters, digits, underscores or hyphens.")
        if role not in ("planner", "worker"):
            raise MessagingError("Choose role planner or worker.")
        peer = replace(identity, team=team, role=role, name=name or identity.name or role)
        with self.locked():
            peers = self.read()
            occupied = [
                item
                for item in peers
                if item.team == team and item.role == role and item.address != peer.address
            ]
            if occupied and not replace_existing:
                raise MessagingError(
                    f"The {role} role in {team} is occupied; use --replace explicitly."
                )
            peers = [
                item for item in peers if item.address != peer.address and item not in occupied
            ]
            self.write([*peers, peer])
        return peer

    def leave(self, address: str) -> bool:
        with self.locked():
            peers = self.read()
            remaining = [peer for peer in peers if peer.address != address]
            self.write(remaining)
        return len(peers) != len(remaining)
