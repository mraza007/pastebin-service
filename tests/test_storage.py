import pytest

from storage import is_valid_id


@pytest.mark.parametrize("good", ["abc123", "AbC9xyz", "shortuuid22chars000000"])
def test_accepts_alphanumeric_ids(good):
    assert is_valid_id(good) is True


@pytest.mark.parametrize(
    "bad", ["", "../etc", "a/b", "a.b", "a b", "..", "x" * 100, "-bad-"]
)
def test_rejects_bad_ids(bad):
    assert is_valid_id(bad) is False
