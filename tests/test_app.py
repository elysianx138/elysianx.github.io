import pytest
from app import app as flask_app
import os


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['SERVER_NAME'] = 'localhost.localdomain'
    with flask_app.test_client() as c:
        yield c


def test_app_imports():
    assert flask_app is not None
    assert flask_app.secret_key is not None
    blueprints = ['user', 'main', 'files', 'articles_bp', 'admin_bp', 'chat', 'api']
    for bp in blueprints:
        assert bp in flask_app.blueprints


def test_homepage_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200


def test_static_folder_exists(client):
    assert os.path.isdir('static')
