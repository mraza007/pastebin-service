from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass

from clock import now

PASTE_DIR = "pastes"

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


def _path(paste_id: str, base_dir: str) -> str:
    return os.path.join(base_dir, f"{paste_id}.json")


def save_paste(paste: Paste, base_dir: str = PASTE_DIR) -> None:
    os.makedirs(base_dir, exist_ok=True)
    with open(_path(paste.id, base_dir), "w", encoding="utf-8") as f:
        json.dump(paste.to_dict(), f)


def load_raw(paste_id: str, base_dir: str = PASTE_DIR) -> Paste | None:
    """Load without applying expiry/burn rules. None if missing/invalid."""
    if not is_valid_id(paste_id):
        return None
    path = _path(paste_id, base_dir)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return Paste.from_dict(json.load(f))


def delete_paste(paste_id: str, base_dir: str = PASTE_DIR) -> None:
    if not is_valid_id(paste_id):
        return
    try:
        os.remove(_path(paste_id, base_dir))
    except FileNotFoundError:
        pass


def load_for_view(paste_id: str, base_dir: str = PASTE_DIR) -> Paste | None:
    """Load applying expiry + burn-after-read. Deletes dead/burned pastes."""
    paste = load_raw(paste_id, base_dir)
    if paste is None:
        return None
    if paste.expires_at is not None and now() > paste.expires_at:
        delete_paste(paste_id, base_dir)
        return None
    if paste.burn_after_read:
        delete_paste(paste_id, base_dir)
    return paste
