import pytest

from storage import Paste, is_valid_id


@pytest.mark.parametrize("good", ["abc123", "AbC9xyz", "shortuuid22chars000000"])
def test_accepts_alphanumeric_ids(good):
    assert is_valid_id(good) is True


@pytest.mark.parametrize(
    "bad", ["", "../etc", "a/b", "a.b", "a b", "..", "x" * 100, "-bad-"]
)
def test_rejects_bad_ids(bad):
    assert is_valid_id(bad) is False


def test_paste_round_trips_through_dict():
    p = Paste(
        id="abc123",
        content="hello",
        language="python",
        render_mode="code",
        created_at=1718800000,
        expires_at=None,
        burn_after_read=False,
        views=0,
    )
    restored = Paste.from_dict(p.to_dict())
    assert restored == p


def test_paste_to_dict_has_all_fields():
    p = Paste(
        id="x",
        content="c",
        language="text",
        render_mode="code",
        created_at=1,
        expires_at=2,
        burn_after_read=True,
        views=3,
    )
    d = p.to_dict()
    assert d == {
        "id": "x",
        "content": "c",
        "language": "text",
        "render_mode": "code",
        "created_at": 1,
        "expires_at": 2,
        "burn_after_read": True,
        "views": 3,
    }
