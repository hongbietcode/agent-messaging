from dataclasses import asdict, dataclass
from uuid import UUID


class MessagingError(ValueError):
    pass


def validate_session_id(value: str) -> str:
    try:
        normalized = str(UUID(value))
    except (ValueError, AttributeError) as error:
        raise MessagingError("Session identity must be a UUID.") from error
    if normalized != value.lower():
        raise MessagingError("Session identity must be a hyphenated UUID.")
    return normalized


@dataclass(frozen=True)
class Peer:
    provider: str
    session_id: str
    profile_dir: str
    cwd: str
    socket_path: str = ""
    native_registry_file: str = ""
    team: str = ""
    role: str = ""
    name: str = ""

    def __post_init__(self) -> None:
        if self.provider not in ("claude", "codex"):
            raise MessagingError("Unknown session provider.")
        validate_session_id(self.session_id)

    @property
    def address(self) -> str:
        return f"{self.provider}:{self.session_id}"

    def to_dict(self) -> dict[str, object]:
        return {**asdict(self), "address": self.address}

    @classmethod
    def from_dict(cls, value: object) -> "Peer":
        if not isinstance(value, dict):
            raise MessagingError("Invalid registry peer.")
        fields = (
            "provider",
            "session_id",
            "profile_dir",
            "cwd",
            "socket_path",
            "native_registry_file",
            "team",
            "role",
            "name",
        )
        if any(not isinstance(value.get(key), str) for key in fields):
            raise MessagingError("Invalid registry peer fields.")
        peer = cls(**{key: value[key] for key in fields})
        if not peer.team or peer.role not in ("planner", "worker"):
            raise MessagingError("Invalid registry role assignment.")
        return peer
