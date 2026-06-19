# Feature-Rich Pastebin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Grow the minimal Flask pastebin into a feature-rich one (expiring pastes, burn-after-read, raw/download, dark mode + theme picker, curl API, Markdown) while keeping its file-based, single-app spirit.

**Architecture:** Pastes are JSON files in `pastes/<id>.json` carrying content + metadata. Storage and rendering are pulled into small modules (`storage.py`, `rendering.py`) so routes in `index.py` stay thin and each piece is unit-testable. Expiry is enforced lazily on read; burn-after-read deletes the file after first view. Markdown output is sanitized with `bleach`. Theming is client-side via a body class + dual Pygments stylesheets.

**Tech Stack:** Python 3.12, Flask, Pygments, shortuuid, markdown, bleach, pytest. Reference design: `docs/plans/2026-06-19-feature-rich-pastebin-design.md`.

**Conventions:** PEP 8, type annotations on all signatures, black/isort/ruff clean. Tests with pytest. Frozen dataclasses where natural. DRY, YAGNI, TDD, frequent commits.

---

## Task 0: Environment & dependencies

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `pytest.ini`

**Step 1: Create `requirements.txt`**

```
flask
shortuuid
pygments
markdown
bleach
```

**Step 2: Create `requirements-dev.txt`**

```
-r requirements.txt
pytest
pytest-cov
```

**Step 3: Create a virtualenv and install**

Run:
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```
Expected: all packages install without error.

**Step 4: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
markers =
    unit: unit tests
    integration: integration tests
```

**Step 5: Verify pytest runs (no tests yet)**

Run: `.venv/bin/pytest -q`
Expected: "no tests ran" (exit 5 is fine).

**Step 6: Commit**

```bash
git add requirements.txt requirements-dev.txt pytest.ini
git commit -m "chore: add dependency and pytest config"
```

> NOTE: Use `.venv/bin/pytest` (or activate the venv) for every test command below.

---

## Task 1: `now()` time helper

Single source of "current time" so expiry is testable without sleeping.

**Files:**
- Create: `clock.py`
- Test: `tests/test_clock.py`

**Step 1: Write the failing test**

```python
# tests/test_clock.py
from clock import now

def test_now_returns_int_unix_seconds():
    value = now()
    assert isinstance(value, int)
    assert value > 1_700_000_000  # after 2023
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_clock.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'clock'`).

**Step 3: Write minimal implementation**

```python
# clock.py
import time


def now() -> int:
    """Current time as integer unix seconds. Patch this in tests."""
    return int(time.time())
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_clock.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add clock.py tests/test_clock.py
git commit -m "feat: add injectable now() clock helper"
```

---

## Task 2: Paste id validation

Reject malformed/path-traversal ids before any filesystem access.

**Files:**
- Create: `storage.py`
- Test: `tests/test_storage.py`

**Step 1: Write the failing test**

```python
# tests/test_storage.py
import pytest
from storage import is_valid_id

@pytest.mark.parametrize("good", ["abc123", "AbC9xyz", "shortuuid22chars000000"])
def test_accepts_alphanumeric_ids(good):
    assert is_valid_id(good) is True

@pytest.mark.parametrize("bad", ["", "../etc", "a/b", "a.b", "a b", "..", "x" * 100, "-bad-"])
def test_rejects_bad_ids(bad):
    assert is_valid_id(bad) is False
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_storage.py -v`
Expected: FAIL (`ImportError: cannot import name 'is_valid_id'`).

**Step 3: Write minimal implementation**

```python
# storage.py
import re

_ID_RE = re.compile(r"^[A-Za-z0-9]{1,40}$")


def is_valid_id(paste_id: str) -> bool:
    """True only for short alphanumeric ids (no path separators/dots)."""
    return bool(_ID_RE.fullmatch(paste_id))
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_storage.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add storage.py tests/test_storage.py
git commit -m "feat: validate paste ids against path traversal"
```

---

## Task 3: Paste dataclass + serialization

**Files:**
- Modify: `storage.py`
- Test: `tests/test_storage.py`

**Step 1: Write the failing test**

```python
# add to tests/test_storage.py
from storage import Paste

def test_paste_round_trips_through_dict():
    p = Paste(
        id="abc123", content="hello", language="python",
        render_mode="code", created_at=1718800000,
        expires_at=None, burn_after_read=False, views=0,
    )
    restored = Paste.from_dict(p.to_dict())
    assert restored == p

def test_paste_to_dict_has_all_fields():
    p = Paste(
        id="x", content="c", language="text", render_mode="code",
        created_at=1, expires_at=2, burn_after_read=True, views=3,
    )
    d = p.to_dict()
    assert d == {
        "id": "x", "content": "c", "language": "text",
        "render_mode": "code", "created_at": 1, "expires_at": 2,
        "burn_after_read": True, "views": 3,
    }
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_storage.py -k paste -v`
Expected: FAIL (`cannot import name 'Paste'`).

**Step 3: Write minimal implementation**

```python
# add to storage.py
from __future__ import annotations
from dataclasses import dataclass, asdict


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
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_storage.py -k paste -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add storage.py tests/test_storage.py
git commit -m "feat: add Paste dataclass with dict serialization"
```

---

## Task 4: save / load paste files

**Files:**
- Modify: `storage.py`
- Test: `tests/test_storage.py`

**Step 1: Write the failing test**

```python
# add to tests/test_storage.py
from storage import save_paste, load_raw

def _make(**kw):
    base = dict(id="abc123", content="hi", language="python",
               render_mode="code", created_at=1, expires_at=None,
               burn_after_read=False, views=0)
    base.update(kw)
    return Paste(**base)

def test_save_then_load_raw(tmp_path):
    p = _make()
    save_paste(p, base_dir=str(tmp_path))
    loaded = load_raw("abc123", base_dir=str(tmp_path))
    assert loaded == p

def test_load_raw_missing_returns_none(tmp_path):
    assert load_raw("doesnotexist", base_dir=str(tmp_path)) is None

def test_load_raw_invalid_id_returns_none(tmp_path):
    assert load_raw("../secret", base_dir=str(tmp_path)) is None
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_storage.py -k "save or load_raw" -v`
Expected: FAIL (`cannot import name 'save_paste'`).

**Step 3: Write minimal implementation**

```python
# add to storage.py
import json
import os

PASTE_DIR = "pastes"


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
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_storage.py -k "save or load_raw" -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add storage.py tests/test_storage.py
git commit -m "feat: persist pastes as JSON files"
```

---

## Task 5: delete + expiry/burn-aware load

**Files:**
- Modify: `storage.py`
- Test: `tests/test_storage.py`

**Step 1: Write the failing test**

```python
# add to tests/test_storage.py
from storage import load_for_view, delete_paste

def test_expired_paste_is_deleted_and_returns_none(tmp_path, monkeypatch):
    import storage
    monkeypatch.setattr(storage, "now", lambda: 1000)
    save_paste(_make(expires_at=500), base_dir=str(tmp_path))
    assert load_for_view("abc123", base_dir=str(tmp_path)) is None
    assert load_raw("abc123", base_dir=str(tmp_path)) is None  # file gone

def test_unexpired_paste_returned(tmp_path, monkeypatch):
    import storage
    monkeypatch.setattr(storage, "now", lambda: 1000)
    save_paste(_make(expires_at=5000), base_dir=str(tmp_path))
    assert load_for_view("abc123", base_dir=str(tmp_path)) is not None

def test_never_expires_when_expires_at_none(tmp_path, monkeypatch):
    import storage
    monkeypatch.setattr(storage, "now", lambda: 10**12)
    save_paste(_make(expires_at=None), base_dir=str(tmp_path))
    assert load_for_view("abc123", base_dir=str(tmp_path)) is not None

def test_burn_after_read_deletes_after_first_view(tmp_path):
    save_paste(_make(burn_after_read=True), base_dir=str(tmp_path))
    first = load_for_view("abc123", base_dir=str(tmp_path))
    assert first is not None
    assert load_for_view("abc123", base_dir=str(tmp_path)) is None  # burned
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_storage.py -k "expired or burn or never or unexpired" -v`
Expected: FAIL (`cannot import name 'load_for_view'`).

**Step 3: Write minimal implementation**

```python
# add to storage.py (import the clock at top of file)
from clock import now


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
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_storage.py -v`
Expected: PASS (all storage tests).

**Step 5: Commit**

```bash
git add storage.py tests/test_storage.py
git commit -m "feat: enforce expiry and burn-after-read on load"
```

---

## Task 6: expiry option → expires_at

Map the form/API expiry choice to an absolute timestamp.

**Files:**
- Modify: `storage.py`
- Test: `tests/test_storage.py`

**Step 1: Write the failing test**

```python
# add to tests/test_storage.py
from storage import compute_expires_at, EXPIRY_OPTIONS

def test_never_returns_none(monkeypatch):
    import storage
    monkeypatch.setattr(storage, "now", lambda: 1000)
    assert compute_expires_at("never") is None

def test_known_option_adds_seconds(monkeypatch):
    import storage
    monkeypatch.setattr(storage, "now", lambda: 1000)
    assert compute_expires_at("1h") == 1000 + 3600

def test_unknown_option_defaults_to_never(monkeypatch):
    import storage
    monkeypatch.setattr(storage, "now", lambda: 1000)
    assert compute_expires_at("bogus") is None

def test_expiry_options_keys():
    assert set(EXPIRY_OPTIONS) >= {"never", "10m", "1h", "1d", "1w"}
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_storage.py -k expir -v`
Expected: FAIL (`cannot import name 'compute_expires_at'`).

**Step 3: Write minimal implementation**

```python
# add to storage.py
EXPIRY_OPTIONS: dict[str, int | None] = {
    "never": None,
    "10m": 10 * 60,
    "1h": 60 * 60,
    "1d": 24 * 60 * 60,
    "1w": 7 * 24 * 60 * 60,
}


def compute_expires_at(option: str) -> int | None:
    """Absolute expiry timestamp for an option, or None for never/unknown."""
    seconds = EXPIRY_OPTIONS.get(option)
    if seconds is None:
        return None
    return now() + seconds
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_storage.py -k expir -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add storage.py tests/test_storage.py
git commit -m "feat: map expiry options to absolute timestamps"
```

---

## Task 7: language validation

**Files:**
- Create: `rendering.py`
- Test: `tests/test_rendering.py`

**Step 1: Write the failing test**

```python
# tests/test_rendering.py
from rendering import normalize_language

def test_known_language_passes_through():
    assert normalize_language("python") == "python"

def test_unknown_language_falls_back_to_text():
    assert normalize_language("not-a-real-lang") == "text"

def test_empty_language_falls_back_to_text():
    assert normalize_language("") == "text"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_rendering.py -v`
Expected: FAIL (`No module named 'rendering'`).

**Step 3: Write minimal implementation**

```python
# rendering.py
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound


def normalize_language(language: str) -> str:
    """Return language if Pygments knows it, else 'text'."""
    try:
        get_lexer_by_name(language)
        return language
    except ClassNotFound:
        return "text"
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_rendering.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add rendering.py tests/test_rendering.py
git commit -m "feat: validate language with text fallback"
```

---

## Task 8: code highlighting + theme CSS

**Files:**
- Modify: `rendering.py`
- Test: `tests/test_rendering.py`

**Step 1: Write the failing test**

```python
# add to tests/test_rendering.py
from rendering import highlight_code, LIGHT_CSS, DARK_CSS

def test_highlight_wraps_in_source_class():
    html = highlight_code("print('hi')", "python")
    assert 'class="source' in html

def test_highlight_unknown_language_does_not_raise():
    html = highlight_code("whatever", "not-real")
    assert "whatever" in html

def test_theme_css_are_scoped_and_distinct():
    assert ".source.light" in LIGHT_CSS
    assert ".source.dark" in DARK_CSS
    assert LIGHT_CSS != DARK_CSS
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_rendering.py -k "highlight or theme" -v`
Expected: FAIL (`cannot import name 'highlight_code'`).

**Step 3: Write minimal implementation**

```python
# add to rendering.py
from pygments import highlight
from pygments.formatters import HtmlFormatter

_LIGHT_FORMATTER = HtmlFormatter(style="default", linenos=True, cssclass="source light")
_DARK_FORMATTER = HtmlFormatter(style="monokai", linenos=True, cssclass="source dark")

LIGHT_CSS = HtmlFormatter(style="default").get_style_defs(".source.light")
DARK_CSS = HtmlFormatter(style="monokai").get_style_defs(".source.dark")


def highlight_code(content: str, language: str) -> str:
    """Highlight code; both light & dark class hooks present for theming."""
    lexer = get_lexer_by_name(normalize_language(language), stripall=True)
    # Render once with both theme classes on the container so CSS can pick.
    formatter = HtmlFormatter(linenos=True, cssclass="source light dark")
    return highlight(content, lexer, formatter)
```

> NOTE for executor: rendering one block with both `light dark` classes plus
> two scoped stylesheets means the active `<body>` theme class decides which
> rules win. Confirm in the browser during Task 13; adjust cssclass strategy if
> specificity collides (fallback: render two blocks, toggle with CSS).

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_rendering.py -k "highlight or theme" -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add rendering.py tests/test_rendering.py
git commit -m "feat: add code highlighting and light/dark theme CSS"
```

---

## Task 9: Markdown rendering with sanitization

**Files:**
- Modify: `rendering.py`
- Test: `tests/test_rendering.py`

**Step 1: Write the failing test**

```python
# add to tests/test_rendering.py
from rendering import render_markdown

def test_markdown_renders_headings():
    html = render_markdown("# Title")
    assert "<h1" in html and "Title" in html

def test_markdown_strips_script_tags():
    html = render_markdown("hello <script>alert(1)</script>")
    assert "<script" not in html
    assert "alert(1)" not in html or "&lt;script" in html

def test_markdown_strips_onclick_attributes():
    html = render_markdown('<a href="x" onclick="evil()">link</a>')
    assert "onclick" not in html

def test_markdown_keeps_safe_links():
    html = render_markdown("[ok](https://example.com)")
    assert 'href="https://example.com"' in html
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_rendering.py -k markdown -v`
Expected: FAIL (`cannot import name 'render_markdown'`).

**Step 3: Write minimal implementation**

```python
# add to rendering.py
import bleach
import markdown as md

_ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS) | {
    "p", "pre", "h1", "h2", "h3", "h4", "h5", "h6",
    "img", "hr", "br", "span", "table", "thead", "tbody",
    "tr", "th", "td",
}
_ALLOWED_ATTRS = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
    "*": ["class"],
}


def render_markdown(content: str) -> str:
    """Render markdown to sanitized HTML (defends against stored XSS)."""
    raw_html = md.markdown(content, extensions=["fenced_code", "tables"])
    return bleach.clean(
        raw_html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        strip=True,
    )
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_rendering.py -k markdown -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add rendering.py tests/test_rendering.py
git commit -m "feat: render markdown with bleach sanitization"
```

---

## Task 10: app factory + create flow (form)

Rewrite `index.py` around the new modules. Start with create + view happy path.

**Files:**
- Modify: `index.py`
- Create: `tests/conftest.py`
- Create: `tests/test_routes.py`

**Step 1: Write conftest + failing test**

```python
# tests/conftest.py
import pytest
from index import create_app

@pytest.fixture
def app(tmp_path):
    app = create_app(paste_dir=str(tmp_path))
    app.config.update(TESTING=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()
```

```python
# tests/test_routes.py
def test_get_index_shows_form(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"<form" in resp.data

def test_create_redirects_to_paste(client):
    resp = client.post("/", data={
        "content": "print('hi')", "language": "python",
        "render_mode": "code", "expiry": "never",
    })
    assert resp.status_code == 303
    location = resp.headers["Location"]
    view = client.get(location)
    assert view.status_code == 200
    assert b"hi" in view.data
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_routes.py -v`
Expected: FAIL (`cannot import name 'create_app'`).

**Step 3: Write minimal implementation**

```python
# index.py
from __future__ import annotations
import os
import shortuuid
from flask import Flask, request, render_template, redirect, abort, url_for

from clock import now
from storage import (
    Paste, save_paste, load_for_view, compute_expires_at, is_valid_id,
)
from rendering import highlight_code, render_markdown, normalize_language, LIGHT_CSS, DARK_CSS

MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB


def create_app(paste_dir: str = "pastes") -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    app.config["PASTE_DIR"] = paste_dir
    os.makedirs(paste_dir, exist_ok=True)

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            content = request.form.get("content", "")
            if not content.strip():
                abort(400)
            render_mode = "markdown" if request.form.get("render_mode") == "markdown" else "code"
            language = normalize_language(request.form.get("language", "text"))
            paste = Paste(
                id=shortuuid.uuid(),
                content=content,
                language=language,
                render_mode=render_mode,
                created_at=now(),
                expires_at=compute_expires_at(request.form.get("expiry", "never")),
                burn_after_read=request.form.get("burn") == "on",
                views=0,
            )
            save_paste(paste, base_dir=app.config["PASTE_DIR"])
            return redirect(url_for("view_paste", paste_id=paste.id), code=303)
        return render_template("index.html")

    @app.route("/<paste_id>")
    def view_paste(paste_id: str):
        if not is_valid_id(paste_id):
            abort(404)
        paste = load_for_view(paste_id, base_dir=app.config["PASTE_DIR"])
        if paste is None:
            abort(404)
        if paste.render_mode == "markdown":
            body = render_markdown(paste.content)
        else:
            body = highlight_code(paste.content, paste.language)
        return render_template(
            "index.html",
            paste_content=body,
            burned=paste.burn_after_read,
            light_css=LIGHT_CSS,
            dark_css=DARK_CSS,
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
```

> NOTE: templates are updated in Task 13; the form test only needs `<form>` to
> exist (current template already has one). If the existing template lacks the
> new fields the create test still passes because they default server-side.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_routes.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add index.py tests/conftest.py tests/test_routes.py
git commit -m "feat: app factory with JSON-backed create and view flow"
```

---

## Task 11: raw + download routes

**Files:**
- Modify: `index.py`
- Test: `tests/test_routes.py`

**Step 1: Write the failing test**

```python
# add to tests/test_routes.py
def _create(client, content="hello world", language="text"):
    resp = client.post("/", data={
        "content": content, "language": language,
        "render_mode": "code", "expiry": "never",
    })
    return resp.headers["Location"].strip("/")

def test_raw_returns_plaintext(client):
    pid = _create(client, "raw body here")
    resp = client.get(f"/raw/{pid}")
    assert resp.status_code == 200
    assert resp.mimetype == "text/plain"
    assert resp.data == b"raw body here"

def test_download_sets_attachment_header(client):
    pid = _create(client, "download me")
    resp = client.get(f"/dl/{pid}")
    assert resp.status_code == 200
    assert "attachment" in resp.headers.get("Content-Disposition", "")

def test_raw_missing_is_404(client):
    assert client.get("/raw/missing404").status_code == 404
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_routes.py -k "raw or download" -v`
Expected: FAIL (404 for `/raw/...` route not defined → actually 404; assert mimetype fails).

**Step 3: Write minimal implementation**

```python
# add inside create_app(), before `return app`
    from flask import Response

    def _load_or_404(paste_id: str):
        if not is_valid_id(paste_id):
            abort(404)
        paste = load_for_view(paste_id, base_dir=app.config["PASTE_DIR"])
        if paste is None:
            abort(404)
        return paste

    @app.route("/raw/<paste_id>")
    def raw_paste(paste_id: str):
        paste = _load_or_404(paste_id)
        return Response(paste.content, mimetype="text/plain")

    @app.route("/dl/<paste_id>")
    def download_paste(paste_id: str):
        paste = _load_or_404(paste_id)
        return Response(
            paste.content,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment; filename={paste_id}.txt"},
        )
```

> NOTE: burn-after-read interacts with raw/dl — each `load_for_view` burns. That
> is acceptable (any access consumes a burn paste). Document this in README.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_routes.py -k "raw or download" -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add index.py tests/test_routes.py
git commit -m "feat: add raw and download routes"
```

---

## Task 12: curl-friendly API + size limit

**Files:**
- Modify: `index.py`
- Test: `tests/test_routes.py`

**Step 1: Write the failing test**

```python
# add to tests/test_routes.py
def test_api_create_returns_url_and_is_retrievable(client):
    resp = client.post("/api/paste", data="hello from curl",
                       query_string={"lang": "text"},
                       content_type="text/plain")
    assert resp.status_code == 201
    url = resp.data.decode().strip()
    assert "/" in url
    pid = url.rstrip("/").split("/")[-1]
    view = client.get(f"/raw/{pid}")
    assert view.data == b"hello from curl"

def test_api_markdown_flag(client):
    resp = client.post("/api/paste?markdown=1", data="# Hi",
                       content_type="text/plain")
    pid = resp.data.decode().strip().rstrip("/").split("/")[-1]
    view = client.get(f"/{pid}")
    assert b"<h1" in view.data

def test_oversized_body_rejected(client):
    big = b"x" * (1 * 1024 * 1024 + 10)
    resp = client.post("/api/paste", data=big, content_type="text/plain")
    assert resp.status_code == 413
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_routes.py -k api -v`
Expected: FAIL (404 / assertion errors — route missing).

**Step 3: Write minimal implementation**

```python
# add inside create_app(), before `return app`
    @app.route("/api/paste", methods=["POST"])
    def api_paste():
        content = request.get_data(as_text=True)
        if not content.strip():
            content = request.form.get("content", "")
        if not content.strip():
            abort(400)
        markdown_flag = request.args.get("markdown") in ("1", "true", "on")
        paste = Paste(
            id=shortuuid.uuid(),
            content=content,
            language=normalize_language(request.args.get("lang", "text")),
            render_mode="markdown" if markdown_flag else "code",
            created_at=now(),
            expires_at=compute_expires_at(request.args.get("expiry", "never")),
            burn_after_read=request.args.get("burn") in ("1", "true", "on"),
            views=0,
        )
        save_paste(paste, base_dir=app.config["PASTE_DIR"])
        url = url_for("view_paste", paste_id=paste.id, _external=True)
        return Response(url + "\n", status=201, mimetype="text/plain")
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_routes.py -k api -v`
Expected: PASS. Then run full suite: `.venv/bin/pytest -q` — all green.

**Step 5: Commit**

```bash
git add index.py tests/test_routes.py
git commit -m "feat: add curl-friendly paste API with size limit"
```

---

## Task 13: templates, theming UI, static CSS

Now make the UI real: base template, theme toggle, create-form controls, paste view.

**Files:**
- Create: `templates/base.html`
- Modify: `templates/index.html`
- Create: `static/style.css`
- Modify: `index.py` (inject theme CSS on all renders)

**Step 1: Manual verification target (no unit test — visual)**

Acceptance criteria to verify in browser:
1. `/` shows content textarea, language `<select>`, render-mode radio (Code/Markdown), expiry `<select>` (10m/1h/1d/1w/never), burn-after-read checkbox, submit.
2. Theme toggle button switches light/dark, persists across reload (localStorage), defaults to `prefers-color-scheme`.
3. A code paste shows highlighted code that is readable in BOTH themes.
4. A markdown paste renders formatted HTML.
5. Paste view shows Raw / Download / New Paste links, and a "burned" notice when applicable.

**Step 2: Implement `templates/base.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pastebin</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
  {% if light_css %}<style>{{ light_css|safe }}</style>{% endif %}
  {% if dark_css %}<style>{{ dark_css|safe }}</style>{% endif %}
  <script>
    (function () {
      var saved = localStorage.getItem('theme');
      var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      var theme = saved || (prefersDark ? 'dark' : 'light');
      document.documentElement.dataset.theme = theme;
    })();
  </script>
</head>
<body class="{{ '' }}">
  <div class="container">
    <header>
      <a href="/" class="brand">Pastebin</a>
      <button id="theme-toggle" type="button">Toggle theme</button>
    </header>
    {% block body %}{% endblock %}
  </div>
  <script>
    document.getElementById('theme-toggle').addEventListener('click', function () {
      var cur = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = cur;
      localStorage.setItem('theme', cur);
    });
  </script>
</body>
</html>
```

**Step 3: Implement `templates/index.html`**

```html
{% extends "base.html" %}
{% block body %}
  {% if not paste_content %}
  <form method="post">
    <textarea name="content" rows="14" required placeholder="Paste here..."></textarea>
    <div class="controls">
      <label>Language
        <select name="language">
          {% for value, label in languages %}
          <option value="{{ value }}" {{ 'selected' if value == 'text' }}>{{ label }}</option>
          {% endfor %}
        </select>
      </label>
      <label>Render
        <select name="render_mode">
          <option value="code">Code</option>
          <option value="markdown">Markdown</option>
        </select>
      </label>
      <label>Expires
        <select name="expiry">
          <option value="never">Never</option>
          <option value="10m">10 minutes</option>
          <option value="1h">1 hour</option>
          <option value="1d">1 day</option>
          <option value="1w">1 week</option>
        </select>
      </label>
      <label class="checkbox"><input type="checkbox" name="burn"> Burn after reading</label>
    </div>
    <button type="submit">Create Paste</button>
  </form>
  {% else %}
  {% if burned %}<p class="notice">This paste was set to burn-after-read and has now been deleted.</p>{% endif %}
  <div class="paste-actions">
    <a href="/raw/{{ paste_id }}">Raw</a>
    <a href="/dl/{{ paste_id }}">Download</a>
    <a href="/">New Paste</a>
  </div>
  <div class="paste-body">{{ paste_content|safe }}</div>
  {% endif %}
{% endblock %}
```

**Step 4: Implement `static/style.css`**

```css
:root {
  --bg: #ffffff; --fg: #1a1a1a; --muted: #666; --border: #ddd; --accent: #2563eb;
}
:root[data-theme="dark"] {
  --bg: #0f1419; --fg: #e6e6e6; --muted: #9aa; --border: #2a2f37; --accent: #60a5fa;
}
body { background: var(--bg); color: var(--fg); font-family: system-ui, sans-serif;
       margin: 0; line-height: 1.6; }
.container { max-width: 900px; margin: 0 auto; padding: 20px; }
header { display: flex; justify-content: space-between; align-items: center;
         border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 20px; }
.brand { font-weight: 700; color: var(--fg); text-decoration: none; }
textarea, select { width: 100%; padding: 10px; background: var(--bg); color: var(--fg);
                   border: 1px solid var(--border); border-radius: 6px; }
.controls { display: flex; flex-wrap: wrap; gap: 12px; margin: 12px 0; }
.controls label { display: flex; flex-direction: column; font-size: 0.85rem; color: var(--muted); }
.controls .checkbox { flex-direction: row; align-items: center; gap: 6px; }
button { background: var(--accent); color: #fff; border: 0; padding: 10px 18px;
         border-radius: 6px; cursor: pointer; }
.paste-actions { display: flex; gap: 14px; margin-bottom: 14px; }
.notice { background: #b9770020; border: 1px solid #b97700; padding: 8px 12px; border-radius: 6px; }
.source { overflow-x: auto; border: 1px solid var(--border); border-radius: 6px; padding: 8px; }
/* Pygments theme blocks are injected; show light by default, dark when toggled */
:root[data-theme="dark"] .source.light { display: none; }
:root:not([data-theme="dark"]) .source.dark { display: none; }
```

> NOTE: The display-toggle approach above expects TWO highlighted blocks (one
> `.source.light`, one `.source.dark`). Update `highlight_code` (Task 8) to
> render both if you choose this strategy, OR keep one block and rely on scoped
> CSS specificity. Pick one and make the browser check in Step 1 pass. Simplest
> robust path: render two blocks.

**Step 5: Pass `languages` + `paste_id` + theme CSS to templates**

Update `index.py` renders: pass `languages=get_language_options()` to the GET form
render, and `paste_id=paste_id`, `light_css=LIGHT_CSS`, `dark_css=DARK_CSS` to the
view render. Add `get_language_options()` (moved from old code) to `rendering.py`
and import it. Re-run the route tests:

Run: `.venv/bin/pytest tests/test_routes.py -v`
Expected: PASS (templates still render; new vars optional/defaulted).

**Step 6: Manual browser check**

Run: `FLASK_DEBUG=1 .venv/bin/flask --app index run`
Verify all 5 acceptance criteria from Step 1. Fix CSS/template until they pass.

**Step 7: Commit**

```bash
git add templates/ static/ index.py rendering.py
git commit -m "feat: themed UI with create controls, raw/download, markdown view"
```

---

## Task 14: optional sweep helper + README

**Files:**
- Modify: `storage.py`
- Test: `tests/test_storage.py`
- Modify: `README.md`

**Step 1: Write the failing test**

```python
# add to tests/test_storage.py
from storage import sweep_expired

def test_sweep_removes_only_expired(tmp_path, monkeypatch):
    import storage
    monkeypatch.setattr(storage, "now", lambda: 1000)
    save_paste(_make(id="alive1", expires_at=5000), base_dir=str(tmp_path))
    save_paste(_make(id="dead1", expires_at=500), base_dir=str(tmp_path))
    removed = sweep_expired(base_dir=str(tmp_path))
    assert removed == 1
    assert load_raw("alive1", base_dir=str(tmp_path)) is not None
    assert load_raw("dead1", base_dir=str(tmp_path)) is None
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_storage.py -k sweep -v`
Expected: FAIL (`cannot import name 'sweep_expired'`).

**Step 3: Write minimal implementation**

```python
# add to storage.py
import glob


def sweep_expired(base_dir: str = PASTE_DIR) -> int:
    """Delete all expired pastes; return count removed. For manual/cron use."""
    removed = 0
    for path in glob.glob(os.path.join(base_dir, "*.json")):
        paste_id = os.path.splitext(os.path.basename(path))[0]
        paste = load_raw(paste_id, base_dir)
        if paste and paste.expires_at is not None and now() > paste.expires_at:
            delete_paste(paste_id, base_dir)
            removed += 1
    return removed
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_storage.py -k sweep -v`
Expected: PASS.

**Step 5: Update README**

Document: features, run instructions (`flask --app index run`, `FLASK_DEBUG`),
the curl API with examples, expiry/burn semantics (incl. raw/dl consuming a burn
paste), and the optional `sweep_expired` cron tip. Keep the blog-post link.

**Step 6: Full suite + commit**

```bash
.venv/bin/pytest -q   # expect ALL green
git add storage.py tests/test_storage.py README.md
git commit -m "feat: add expired-paste sweep helper and update docs"
```

---

## Task 15: final verification

**Step 1: Run full suite with coverage**

Run: `.venv/bin/pytest --cov=. --cov-report=term-missing -q`
Expected: all tests pass; review coverage for storage/rendering/routes.

**Step 2: Lint/format (if tooling present)**

Run: `.venv/bin/ruff check . && .venv/bin/black --check . && .venv/bin/isort --check .`
(If not installed, skip — not a blocker.)

**Step 3: Manual smoke test**

- Create code paste → view → raw → download.
- Create markdown paste with a `<script>` → confirm it is NOT executed.
- Create burn-after-read paste → view twice → second view 404s.
- Create 10m-expiry paste → confirm it views now (expiry verified by unit tests).
- Toggle theme → reload → theme persists.
- `curl --data-binary @index.py "http://localhost:5000/api/paste?lang=python"` → open URL.

**Step 4: Final commit if any cleanup**

```bash
git add -A && git commit -m "chore: final cleanup and verification"
```

---

## Done criteria

- All pytest tests green; storage/rendering/routes covered.
- All 6 features work end-to-end (expiry, burn, raw/download, theme, API, markdown).
- Markdown XSS sanitization verified (automated + manual).
- `debug` off by default; size limit enforced; ids validated.
- README documents features + curl usage.
