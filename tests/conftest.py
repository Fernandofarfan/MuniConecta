import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def cliente():
    from app.main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def _setup_env():
    os.environ.setdefault("JWT_SECRET", "test-secret")


@pytest.fixture
def api_key():
    return os.getenv("API_KEY", "")


@pytest.fixture
def headers(api_key):
    return {"X-API-Key": api_key}
