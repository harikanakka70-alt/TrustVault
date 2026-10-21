import os
import tempfile
from pathlib import Path
import jwt
from datetime import datetime, timedelta, timezone

test_db = Path(tempfile.gettempdir()) / "trustvault_test.db"
test_db.unlink(missing_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{test_db.as_posix()}"
os.environ["TRUSTVAULT_SECRET_KEY"] = "test-only-secret-for-automated-tests"
os.environ["TRUSTVAULT_ADMIN_USERNAME"] = "test_admin"
os.environ["TRUSTVAULT_ADMIN_EMAIL"] = "test_admin@example.com"
os.environ["TRUSTVAULT_ADMIN_PASSWORD"] = "TestAdminPass123!"

from fastapi.testclient import TestClient
from main import app, create_bootstrap_admin

client = TestClient(app)
create_bootstrap_admin()


def register_user(username, email):
    return client.post(
        "/register",
        json={
            "username": username,
            "email": email,
            "password": "StrongTestPass123!",
        },
    )


def login_user(username, password="StrongTestPass123!"):
    response = client.post(
        "/login",
        json={
            "username": username,
            "password": password,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


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
    assert register_user(
        "viewer_test", "viewer_test@example.com"
    ).status_code == 201

    token = login_user("viewer_test")

    response = client.post(
        "/admin/users/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "viewer_test", "role": "admin"},
    )
    assert response.status_code == 403


def test_viewer_cannot_upload_document():
    assert register_user(
        "upload_viewer", "upload_viewer@example.com"
    ).status_code == 201

    token = login_user("upload_viewer")

    response = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"name": "test.txt", "category": "test"},
        files={"file": ("test.txt", b"test content", "text/plain")},
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
    assert register_user(
        "idor_viewer", "idor_viewer@example.com"
    ).status_code == 201

    token = login_user("idor_viewer")

    response = client.get(
        "/documents/999999/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (403, 404)

def test_viewer_cannot_download_another_users_document():
    owner_registration = register_user(
        "idor_owner", "idor_owner@example.com"
    )
    assert owner_registration.status_code == 201

    viewer_registration = register_user(
        "idor_other", "idor_other@example.com"
    )
    assert viewer_registration.status_code == 201

    # Log in as the configured test admin and promote the document owner.
    admin_token = login_user("test_admin", "TestAdminPass123!")

    role_response = client.post(
        "/admin/users/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "idor_owner", "role": "owner"},
    )
    assert role_response.status_code == 200, role_response.text

    owner_token = login_user("idor_owner")
    viewer_token = login_user("idor_other")

    upload_response = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        data={"name": "private_test.txt", "category": "test"},
        files={
            "file": (
                "private_test.txt",
                b"private test content",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    download_response = client.get(
        f"/documents/{document_id}/download",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert download_response.status_code in (403, 404)

def test_revoked_permission_blocks_download():
    # Create a document owner and a viewer
    assert register_user(
        "revoke_owner", "revoke_owner@example.com"
    ).status_code == 201

    assert register_user(
        "revoke_viewer", "revoke_viewer@example.com"
    ).status_code == 201

    owner_token = login_user("revoke_owner")
    viewer_token = login_user("revoke_viewer")

    owner_headers = {
        "Authorization": f"Bearer {owner_token}"
    }
    viewer_headers = {
        "Authorization": f"Bearer {viewer_token}"
    }

    # Promote the owner using the test admin
    admin_token = login_user("test_admin", "TestAdminPass123!")
    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    role_response = client.post(
        "/admin/users/role",
        headers=admin_headers,
        json={"username": "revoke_owner", "role": "owner"},
    )
    assert role_response.status_code == 200, role_response.text

    # Upload a private document
    upload_response = client.post(
        "/documents/upload",
        headers=owner_headers,
        data={
            "name": "Revocation Test",
            "category": "test",
            "owner_id": "1",
        },
        files={"file": ("revoke_test.txt", b"private test content", "text/plain")},
    )
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    # Grant read permission to the viewer
    grant_response = client.post(
        f"/documents/{document_id}/permissions",
        headers=owner_headers,
        json={"username": "revoke_viewer", "access_level": "read"},
    )
    assert grant_response.status_code == 200, grant_response.text

    # Confirm the viewer can download before revocation
    before_revoke = client.get(
        f"/documents/{document_id}/download",
        headers=viewer_headers,
    )
    assert before_revoke.status_code == 200, before_revoke.text

    # Revoke permission
    revoke_response = client.delete(
        f"/documents/{document_id}/permissions/revoke_viewer",
        headers=owner_headers,
    )
    assert revoke_response.status_code == 200, revoke_response.text

    # Confirm access is denied after revocation
    after_revoke = client.get(
        f"/documents/{document_id}/download",
        headers=viewer_headers,
    )
    assert after_revoke.status_code in (403, 404), after_revoke.text  
