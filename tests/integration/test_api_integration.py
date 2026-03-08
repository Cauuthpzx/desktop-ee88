"""
Integration tests — FastAPI endpoints qua TestClient.
Test full flow: register → login → me → refresh.
Cần: pip install httpx
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """FastAPI TestClient — mock database dependency."""
    try:
        from httpx import ASGITransport
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("httpx not installed")

    # Mock database
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    def fake_get_db():
        yield mock_conn

    from server.main import app
    from server.database import get_db
    app.dependency_overrides[get_db] = fake_get_db

    with TestClient(app) as c:
        yield c, mock_cursor

    app.dependency_overrides.clear()


@pytest.mark.integration
class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        c, _ = client
        resp = c.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True


@pytest.mark.integration
class TestRegisterEndpoint:
    def test_register_success(self, client):
        c, mock_cur = client
        mock_cur.fetchone.return_value = None  # username not taken
        resp = c.post("/api/register", json={
            "username": "newuser",
            "password": "123456",
        })
        assert resp.status_code == 200

    def test_register_reserved_username(self, client):
        c, _ = client
        resp = c.post("/api/register", json={
            "username": "admin",
            "password": "123456",
        })
        data = resp.json()
        assert data["ok"] is False

    def test_register_short_password(self, client):
        c, _ = client
        resp = c.post("/api/register", json={
            "username": "newuser",
            "password": "123",
        })
        assert resp.status_code == 422  # Pydantic validation

    def test_register_short_username(self, client):
        c, _ = client
        resp = c.post("/api/register", json={
            "username": "ab",
            "password": "123456",
        })
        assert resp.status_code == 422


@pytest.mark.integration
class TestLoginEndpoint:
    def test_login_user_not_found(self, client):
        c, mock_cur = client
        mock_cur.fetchone.return_value = None
        resp = c.post("/api/login", json={
            "username": "nobody",
            "password": "123456",
        })
        data = resp.json()
        assert data["ok"] is False
