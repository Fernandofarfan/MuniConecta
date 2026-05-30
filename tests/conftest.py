import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://mock.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "mock-key")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ["DEMO_MODE"] = "false"


@pytest.fixture
def cliente():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def api_key():
    return os.getenv("API_KEY", "")


@pytest.fixture
def headers(api_key):
    return {"X-API-Key": api_key}
