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
