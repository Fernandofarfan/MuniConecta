import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def cliente():
    from app.main import app

    return TestClient(app)


@pytest.fixture
def api_key():
    import os

    return os.getenv("API_KEY", "")


@pytest.fixture
def headers(api_key):
    return {"X-API-Key": api_key}
