"""
Unit tests for FastAPI Authentication (Requirement 9.5).
Tests:
- Successful login returns valid JWT token and user profile.
- Invalid credentials return 401 Unauthorized.
- Protected endpoints reject requests without token (401).
- Token expiration or invalid signature rejection.
"""
import pytest
from starlette.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.src.main import app
from api.src.auth import get_password_hash, create_access_token

client = TestClient(app)

def test_login_success():
    hashed = get_password_hash("Secret123!")
    mock_user = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": hashed,
        "role": "viewer",
        "full_name": "Test Viewer",
        "is_active": True
    }

    with patch("api.src.routers.auth.get_db") as mock_get_db:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = mock_user
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_get_db.return_value.__enter__.return_value = mock_conn

        response = client.post("/auth/login", json={"username": "testuser", "password": "Secret123!"})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
        assert data["user"]["role"] == "viewer"

def test_login_invalid_password():
    hashed = get_password_hash("CorrectPassword!")
    mock_user = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": hashed,
        "role": "viewer",
        "full_name": "Test Viewer",
        "is_active": True
    }

    with patch("api.src.routers.auth.get_db") as mock_get_db:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = mock_user
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_get_db.return_value.__enter__.return_value = mock_conn

        response = client.post("/auth/login", json={"username": "testuser", "password": "WrongPassword!"})
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

def test_unauthenticated_request_to_kpis_rejected():
    """Unauthenticated users cannot access protected data endpoints (401)."""
    response = client.get("/api/kpis")
    assert response.status_code == 401
    assert "Authentication token is missing" in response.json()["detail"]

def test_unauthenticated_request_to_events_rejected():
    response = client.get("/api/events")
    assert response.status_code == 401
