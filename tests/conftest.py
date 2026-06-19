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
