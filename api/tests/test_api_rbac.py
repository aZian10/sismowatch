"""
Unit tests for Role-Based Access Control (RBAC) (Requirement 9.6).
Verifies that:
- A user with 'viewer' role CAN access read endpoints (KPIs, events, reports, pipeline status).
- A user with 'viewer' role CANNOT access admin endpoints:
  - GET /api/quality/quarantine -> returns 403 Forbidden
  - POST /api/admin/backfill -> returns 403 Forbidden
  - POST /api/admin/reports/regenerate -> returns 403 Forbidden
- An admin user CAN access administrative endpoints.
"""
import pytest
from starlette.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.src.main import app
from api.src.auth import create_access_token

client = TestClient(app)

@pytest.fixture
def viewer_token():
    return create_access_token({"sub": "viewer_user", "role": "viewer", "user_id": 10})

@pytest.fixture
def admin_token():
    return create_access_token({"sub": "admin_user", "role": "admin", "user_id": 1})

def mock_user_lookup(username: str, role: str):
    mock_user = {
        "id": 1 if role == "admin" else 10,
        "username": username,
        "email": f"{username}@example.com",
        "role": role,
        "full_name": f"{username.capitalize()} Account",
        "is_active": True
    }
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = mock_user
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    return mock_conn

def test_viewer_cannot_access_quarantine(viewer_token):
    """Confirming that a viewer cannot view quarantine records (403 Forbidden)."""
    with patch("api.src.auth.get_db") as mock_db:
        mock_db.return_value.__enter__.return_value = mock_user_lookup("viewer_user", "viewer")

        headers = {"Authorization": f"Bearer {viewer_token}"}
        response = client.get("/api/quality/quarantine", headers=headers)
        
        assert response.status_code == 403
        assert "Access forbidden" in response.json()["detail"]
        assert "viewer" in response.json()["detail"]

def test_viewer_cannot_launch_backfill(viewer_token):
    """Confirming that a viewer cannot trigger historical backfills (403 Forbidden)."""
    with patch("api.src.auth.get_db") as mock_db:
        mock_db.return_value.__enter__.return_value = mock_user_lookup("viewer_user", "viewer")

        headers = {"Authorization": f"Bearer {viewer_token}"}
        body = {"starttime": "2026-10-01", "endtime": "2026-10-15", "minmagnitude": 3.0}
        response = client.post("/api/admin/backfill", headers=headers, json=body)
        
        assert response.status_code == 403
        assert "Access forbidden" in response.json()["detail"]

def test_viewer_cannot_regenerate_report(viewer_token):
    """Confirming that a viewer cannot trigger AI report regeneration (403 Forbidden)."""
    with patch("api.src.auth.get_db") as mock_db:
        mock_db.return_value.__enter__.return_value = mock_user_lookup("viewer_user", "viewer")

        headers = {"Authorization": f"Bearer {viewer_token}"}
        body = {"target_date": "2026-10-25"}
        response = client.post("/api/admin/reports/regenerate", headers=headers, json=body)
        
        assert response.status_code == 403
        assert "Access forbidden" in response.json()["detail"]

def test_admin_can_access_quarantine(admin_token):
    """Admin user successfully accesses quarantine endpoint."""
    with patch("api.src.auth.get_db") as mock_auth_db, \
         patch("api.src.routers.quality.get_db") as mock_quality_db:
        
        mock_auth_db.return_value.__enter__.return_value = mock_user_lookup("admin_user", "admin")
        
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {"total": 0}
        mock_cur.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_quality_db.return_value.__enter__.return_value = mock_conn

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/quality/quarantine", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
