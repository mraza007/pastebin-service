def _create(client, content="hello world", language="text"):
    resp = client.post(
        "/",
        data={
            "content": content,
            "language": language,
            "render_mode": "code",
            "expiry": "never",
        },
    )
    return resp.headers["Location"].strip("/")


def test_get_index_shows_form(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"<form" in resp.data


def test_create_redirects_to_paste(client):
    resp = client.post(
        "/",
        data={
            "content": "print('hi')",
            "language": "python",
            "render_mode": "code",
            "expiry": "never",
        },
    )
    assert resp.status_code == 303
    location = resp.headers["Location"]
    view = client.get(location)
    assert view.status_code == 200
    assert b"hi" in view.data


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
