import re

_ID_RE = re.compile(r"^[A-Za-z0-9]{1,40}$")


def is_valid_id(paste_id: str) -> bool:
    """True only for short alphanumeric ids (no path separators/dots)."""
    return bool(_ID_RE.fullmatch(paste_id))
