from __future__ import annotations

import re
from dataclasses import asdict, dataclass

_ID_RE = re.compile(r"^[A-Za-z0-9]{1,40}$")


def is_valid_id(paste_id: str) -> bool:
    """True only for short alphanumeric ids (no path separators/dots)."""
    return bool(_ID_RE.fullmatch(paste_id))


@dataclass(frozen=True)
class Paste:
    id: str
    content: str
    language: str
    render_mode: str  # "code" | "markdown"
    created_at: int
    expires_at: int | None
    burn_after_read: bool
    views: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Paste":
        return cls(**data)
