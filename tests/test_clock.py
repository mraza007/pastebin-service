from clock import now


def test_now_returns_int_unix_seconds():
    value = now()
    assert isinstance(value, int)
    assert value > 1_700_000_000  # after 2023
