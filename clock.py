import time


def now() -> int:
    """Current time as integer unix seconds. Patch this in tests."""
    return int(time.time())
