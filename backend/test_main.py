
import os
import tempfile
from pathlib import Path
import jwt
from datetime import datetime, timedelta, timezone

# Use a separate database for automated tests.
test_db = Path(tempfile.gettempdir()) / "trustvault_test.db"
test_db.unlink(missing_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{test_db.as_posix()}"
os.environ["TRUSTVAULT_SECRET_KEY"] = (
    "test-only-secret-for-automated-tests"
)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200


def test_short_password_rejected():
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",
        },
    )
    assert response.status_code == 400


def test_forged_token_rejected():
    response = client.get(
        "/documents",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_viewer_cannot_change_user_role():
    register_response = client.post(
        "/register",
        json={
            "username": "viewer_test",
            "email": "viewer_test@example.com",
            "password": "StrongTestPass123!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/login",
        json={
            "username": "viewer_test",
            "password": "StrongTestPass123!",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/admin/users/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "viewer_test", "role": "admin"},
    )
    assert response.status_code == 403


def test_viewer_cannot_upload_document():
    register_response = client.post(
        "/register",
        json={
            "username": "upload_viewer",
            "email": "upload_viewer@example.com",
            "password": "StrongTestPass123!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/login",
        json={
            "username": "upload_viewer",
            "password": "StrongTestPass123!",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"name": "test.txt", "category": "test"},
        files={
            "file": ("test.txt", b"test content", "text/plain")
        },
    )
    assert response.status_code == 403


def test_expired_token_rejected():
    expired_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        os.environ["TRUSTVAULT_SECRET_KEY"],
        algorithm="HS256",
    )

    response = client.get(
        "/documents",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_viewer_cannot_download_unpermitted_document():
    register_response = client.post(
        "/register",
        json={
            "username": "idor_viewer",
            "email": "idor_viewer@example.com",
            "password": "StrongTestPass123!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/login",
        json={
            "username": "idor_viewer",
            "password": "StrongTestPass123!",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/documents/999999/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (403, 404)
