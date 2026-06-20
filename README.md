# PasteBin Service

A small, file-backed pastebin built with Flask. Each paste is stored as a JSON
file under `pastes/` carrying its content and metadata — no database required.

Original write-up: [muhammadraza.me](https://muhammadraza.me/2024/Simple-Pastebin-In-Python/)

## Features

- **Syntax highlighting** for hundreds of languages (Pygments).
- **Markdown rendering** — paste Markdown and view it as formatted, **sanitized**
  HTML (untrusted HTML/scripts are stripped to prevent stored XSS).
- **Expiring pastes** — choose `10m`, `1h`, `1d`, `1w`, or `never`. Expired
  pastes are deleted lazily on access.
- **Burn after reading** — the paste is deleted the first time it is viewed.
- **Raw view & download** — `/raw/<id>` (plain text) and `/dl/<id>` (file
  download).
- **Dark mode** with a theme toggle (remembered via `localStorage`, defaults to
  your OS preference). Code colors adapt to the active theme.
- **Curl-friendly API** for creating pastes from the terminal.

## Running

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
FLASK_APP=index .venv/bin/flask run
```

The server runs with the debugger **off** by default. Enable it only for local
development:

```bash
FLASK_DEBUG=1 FLASK_APP=index .venv/bin/flask run
```

Pastes are written to `./pastes` by default.

## Docker

Run the whole thing with Docker Compose (served by gunicorn):

```bash
docker compose up --build
```

Then open **http://localhost:5001**. The app listens on port 5000 inside the
container; the host port is mapped to **5001** because macOS AirPlay Receiver
occupies 5000 (it returns `403`). Change the mapping in `docker-compose.yml` if
you prefer a different host port.

Pastes persist across restarts in the named `pastes` volume (mounted at
`/app/pastes`). To stop and remove the container:

```bash
docker compose down          # keep the pastes volume
docker compose down -v       # also delete stored pastes
```

## API

Create a paste by POSTing the body to `/api/paste`. The response is the paste
URL (plus a trailing newline), so it pipes cleanly:

```bash
# From a file, as Python
curl --data-binary @main.py "http://localhost:5000/api/paste?lang=python"

# From stdin
echo "hello" | curl --data-binary @- "http://localhost:5000/api/paste"
```

Optional query parameters:

| Param      | Values                              | Default |
|------------|-------------------------------------|---------|
| `lang`     | any Pygments alias (`python`, `go`) | `text`  |
| `expiry`   | `never`, `10m`, `1h`, `1d`, `1w`    | `never` |
| `burn`     | `1` / `true` / `on`                 | off     |
| `markdown` | `1` / `true` / `on`                 | off     |

Bodies larger than 1 MB are rejected with `413 Payload Too Large`.

## Expiry & burn semantics

- Expiry is enforced **lazily**: a paste past its `expires_at` is deleted the
  next time it is requested (returning `404`).
- **Burn-after-read** deletes the paste on its first access. Note that `/raw`
  and `/dl` also count as an access, so fetching either one consumes a
  burn-after-read paste.

To purge expired pastes proactively (e.g. from cron), call `sweep_expired()`:

```bash
.venv/bin/python -c "import storage; print(storage.sweep_expired())"
```

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```
