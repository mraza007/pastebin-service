import pytest

import storage
from storage import (
    Paste,
    is_valid_id,
    load_for_view,
    load_raw,
    save_paste,
)


def _make(**kw):
    base = dict(
        id="abc123",
        content="hi",
        language="python",
        render_mode="code",
        created_at=1,
        expires_at=None,
        burn_after_read=False,
        views=0,
    )
    base.update(kw)
    return Paste(**base)


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


def test_save_then_load_raw(tmp_path):
    p = _make()
    save_paste(p, base_dir=str(tmp_path))
    loaded = load_raw("abc123", base_dir=str(tmp_path))
    assert loaded == p


def test_load_raw_missing_returns_none(tmp_path):
    assert load_raw("doesnotexist", base_dir=str(tmp_path)) is None


def test_load_raw_invalid_id_returns_none(tmp_path):
    assert load_raw("../secret", base_dir=str(tmp_path)) is None


def test_expired_paste_is_deleted_and_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "now", lambda: 1000)
    save_paste(_make(expires_at=500), base_dir=str(tmp_path))
    assert load_for_view("abc123", base_dir=str(tmp_path)) is None
    assert load_raw("abc123", base_dir=str(tmp_path)) is None  # file gone


def test_unexpired_paste_returned(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "now", lambda: 1000)
    save_paste(_make(expires_at=5000), base_dir=str(tmp_path))
    assert load_for_view("abc123", base_dir=str(tmp_path)) is not None


def test_never_expires_when_expires_at_none(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "now", lambda: 10**12)
    save_paste(_make(expires_at=None), base_dir=str(tmp_path))
    assert load_for_view("abc123", base_dir=str(tmp_path)) is not None


def test_burn_after_read_deletes_after_first_view(tmp_path):
    save_paste(_make(burn_after_read=True), base_dir=str(tmp_path))
    first = load_for_view("abc123", base_dir=str(tmp_path))
    assert first is not None
    assert load_for_view("abc123", base_dir=str(tmp_path)) is None  # burned
