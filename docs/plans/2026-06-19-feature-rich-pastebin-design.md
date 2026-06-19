# Feature-Rich Pastebin — Design

Date: 2026-06-19

## Goal

Grow the minimal Flask pastebin into a feature-rich one while keeping the
file-based, single-app spirit of the original (the companion to the blog post).
No database, no framework sprawl — just a few small, testable modules.

## Features in scope

| Feature | Mechanism |
|---|---|
| Expiring pastes | absolute `expires_at`, lazy delete on read |
| Burn after reading | `burn_after_read` flag, delete after first view |
| Raw / download | `/raw/<id>`, `/dl/<id>` |
| Dark mode + theme picker | dual Pygments CSS + `localStorage` toggle |
| Curl-friendly API | `POST /api/paste` returns the URL as plain text |
| Markdown rendering | `markdown` + `bleach` sanitize |
| Hardening (cheap, high value) | lexer validation, id validation, debug off by default, size cap |

## Data model & storage

Each paste is stored as `pastes/<id>.json`:

```json
{
  "id": "abc123",
  "content": "raw text the user submitted",
  "language": "python",
  "render_mode": "code",        // "code" | "markdown"
  "created_at": 1718800000,     // unix seconds
  "expires_at": 1718886400,     // unix seconds, or null = never
  "burn_after_read": false,
  "views": 0
}
```

Design notes:

- `render_mode` decouples *how we display* from *language*. Markdown is a render
  mode, not a Pygments lexer; when `render_mode == "markdown"`, `language` is
  ignored. The create form gets a "Render as: Code / Markdown" choice.
- `expires_at` is absolute, computed at create time from the chosen TTL. Storing
  absolute (not a relative TTL) makes expiry a trivial `now > expires_at` check.
- `burn_after_read` + `views` drive burn-after-reading: on view, if the burn flag
  is set, serve once then delete the file.

Expiry enforcement is **lazy**: on request, check `expires_at`/burn and
delete-then-404 if dead. No background job or cron required — keeps the service
dependency-free. An optional `sweep_expired()` helper exists for manual/cron use
but is not needed for correctness.

All JSON reads/writes go through `save_paste(dict)` and `load_paste(id)` so the
format lives in exactly one place.

## Routes & request flow

```
GET  /                 → create form (expiry, render-mode, burn controls)
POST /                 → create paste (browser form) → 303 redirect to /<id>
GET  /<id>             → rendered view (highlighted code or sanitized markdown)
GET  /raw/<id>         → text/plain, original content verbatim
GET  /dl/<id>          → same bytes, Content-Disposition: attachment
POST /api/paste        → curl-friendly create; returns the URL as plain text
```

**Create flow (browser):** form posts `content`, `language`, `render_mode`,
`expiry` (select: 10m / 1h / 1d / 1w / never), `burn` (checkbox). Server
validates, computes `expires_at`, writes JSON, then **redirects (303) to
`/<id>`**. This replaces the current "re-render the form with the URL printed"
behavior. Redirect-after-POST lands the user on the new paste's permalink:
refresh-safe and immediately shareable.

**View flow:** `load_paste(id)` → missing → 404; expired → delete + 404; else
render by `render_mode`. If `burn_after_read`, render once then delete the file
and show a "this paste has now been burned" notice.

**Curl API:** `POST /api/paste` accepts a raw body
(`curl --data-binary @file`) or form fields, plus optional query params
`?lang=`, `?expiry=`, `?burn=1`, `?markdown=1`. Responds with just the URL +
newline so pipe ergonomics work:

```
curl --data-binary @main.py https://host/api/paste?lang=python
```

**Limits:** `MAX_CONTENT_LENGTH` (≈1 MB) rejects oversized bodies cheaply for
both form and API (→ 413).

## Rendering, theming & security

**Syntax highlighting + real dark mode.** Render code with CSS classes and ship
two scoped theme blocks generated once at startup:

```python
LIGHT_CSS = HtmlFormatter(style="default").get_style_defs(".source.light")
DARK_CSS  = HtmlFormatter(style="monokai").get_style_defs(".source.dark")
```

The page toggles a `light`/`dark` class on `<body>`. CSS variables handle page
chrome (bg, text, borders); the matching `.source` block handles code colors.
The theme picker is a small JS toggle persisting choice in `localStorage`,
defaulting to the OS `prefers-color-scheme`. No server round-trip to switch.

**Markdown.** Render with the `markdown` library, then **sanitize output with
`bleach`** (allowlist of tags/attributes). Non-negotiable: markdown permits raw
HTML/`<script>`, so unsanitized output is a stored-XSS hole. Pygments output is
controlled/safe, so only markdown needs the bleach pass.

**Hardening baked in:**

- `get_lexer_by_name` currently takes user input directly and 500s on unknown
  languages. Validate `language` against the known lexer set on create; fall back
  to `text`.
- Validate `paste_id` shape (alphanumeric) before any filesystem access to
  prevent path traversal (`../`); always `os.path.join` under `PASTE_DIR` with a
  basename check.
- `debug=True` becomes env-driven (`FLASK_DEBUG`), off by default — shipping with
  the Werkzeug debugger open is a remote-code-execution risk.

**Dependencies added:** `markdown`, `bleach` (`flask`, `shortuuid`, `pygments`
already used). Add a `requirements.txt` (none exists today).

## File structure

```
pastebin-service/
  index.py              # app + routes
  storage.py            # save_paste / load_paste / sweep_expired / id validation
  rendering.py          # highlight_code / render_markdown(+sanitize) / theme CSS
  templates/
    index.html          # create form + paste view (extends base)
    base.html           # head, theme toggle JS, CSS variables
  static/
    style.css           # page chrome + light/dark variables
  tests/
    test_storage.py
    test_routes.py
    test_rendering.py
  requirements.txt
  README.md
```

Pulling `storage` and `rendering` out of `index.py` keeps routes thin and each
piece independently testable. Still tiny — three small modules, not a framework.

## Testing (pytest)

- `test_storage.py` — round-trip save/load; expired paste returns `None` and is
  deleted; burn-after-read deletes on second access; id validation rejects `../`
  and malformed input.
- `test_rendering.py` — code highlighting produces `.source` markup; **markdown
  sanitization strips `<script>`** (security-critical); unknown language falls
  back to `text`.
- `test_routes.py` — Flask test client: create → 303 redirect → view happy path;
  `/raw` returns `text/plain`; `/dl` sets attachment header; `/api/paste` returns
  a URL and the paste is retrievable; oversized body → 413; expired paste → 404.

**Time handling:** expiry logic reads `now` from a single injectable helper so
tests can simulate the future without sleeping.
```
