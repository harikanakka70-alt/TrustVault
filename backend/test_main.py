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
        files={"file": ("revoke_test.txt", b"private test content","text/plain")},
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

def test_non_owner_cannot_grant_document_permission():
    # Register two users
    assert register_user(
        "t3_owner", "t3_owner@example.com"
    ).status_code == 201

    assert register_user(
        "t3_other", "t3_other@example.com"
    ).status_code == 201

    owner_token = login_user("t3_owner")
    other_token = login_user("t3_other")
    admin_token = login_user("test_admin", "TestAdminPass123!")

    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }
    owner_headers = {
        "Authorization": f"Bearer {owner_token}"
    }
    other_headers = {
        "Authorization": f"Bearer {other_token}"
    }

    # Promote the document owner and the other user
    for username, role in [
        ("t3_owner", "owner"),
        ("t3_other", "owner"),
    ]:
        response = client.post(
            "/admin/users/role",
            headers=admin_headers,
            json={"username": username, "role": role},
        )
        assert response.status_code == 200, response.text

    # The owner uploads a private document
    upload = client.post(
        "/documents/upload",
        headers=owner_headers,
        data={
            "name": "T3 Permission Test",
            "category": "test",
        },
        files={
            "file": (
                "t3_test.txt",
                b"private test content",
                "text/plain",
            )
        },
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["document_id"]

    # Another owner must not grant access to this document
    response = client.post(
        f"/documents/{document_id}/permissions",
        headers=other_headers,
        json={
            "username": "t3_owner",
            "access_level": "read",
        },
    )
    assert response.status_code == 403, response.text



def test_non_owner_cannot_edit_another_users_document():
    assert register_user(
        "edit_owner", "edit_owner@example.com"
    ).status_code == 201
    assert register_user(
        "edit_attacker", "edit_attacker@example.com"
    ).status_code == 201

    admin_token = login_user("test_admin", "TestAdminPass123!")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    promote = client.post(
        "/admin/users/role",
        headers=admin_headers,
        json={"username": "edit_owner", "role": "owner"},
    )
    assert promote.status_code == 200, promote.text

    owner_token = login_user("edit_owner")
    attacker_token = login_user("edit_attacker")

    upload = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        data={"name": "Private Edit Test", "category": "test"},
        files={"file": ("private_edit.txt", b"private content", "text/plain")},
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["document_id"]

    response = client.put(
        f"/documents/{document_id}",
        headers={"Authorization": f"Bearer {attacker_token}"},
        json={"name": "Hacked Name", "category": "changed"},
    )
    assert response.status_code == 403, response.text


def test_non_owner_cannot_delete_another_users_document():
    assert register_user(
        "delete_owner", "delete_owner@example.com"
    ).status_code == 201
    assert register_user(
        "delete_attacker", "delete_attacker@example.com"
    ).status_code == 201

    admin_token = login_user("test_admin", "TestAdminPass123!")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    promote = client.post(
        "/admin/users/role",
        headers=admin_headers,
        json={"username": "delete_owner", "role": "owner"},
    )
    assert promote.status_code == 200, promote.text

    owner_token = login_user("delete_owner")
    attacker_token = login_user("delete_attacker")

    upload = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        data={"name": "Private Delete Test", "category": "test"},
        files={"file": ("private_delete.txt", b"private content", "text/plain")},
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["document_id"]

    response = client.delete(
        f"/documents/{document_id}",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    assert response.status_code == 403, response.text

    # Verify the document still exists and its owner can still download it.
    owner_download = client.get(
        f"/documents/{document_id}/download",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_download.status_code == 200, owner_download.text


def test_read_permission_cannot_edit_document():
    assert register_user(
        "readonly_owner", "readonly_owner@example.com"
    ).status_code == 201
    assert register_user(
        "readonly_user", "readonly_user@example.com"
    ).status_code == 201

    admin_token = login_user("test_admin", "TestAdminPass123!")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    promote = client.post(
        "/admin/users/role",
        headers=admin_headers,
        json={"username": "readonly_owner", "role": "owner"},
    )
    assert promote.status_code == 200, promote.text

    owner_token = login_user("readonly_owner")
    readonly_token = login_user("readonly_user")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    readonly_headers = {"Authorization": f"Bearer {readonly_token}"}

    upload = client.post(
        "/documents/upload",
        headers=owner_headers,
        data={"name": "Read Only Test", "category": "test"},
        files={"file": ("readonly.txt", b"original content", "text/plain")},
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["document_id"]

    grant = client.post(
        f"/documents/{document_id}/permissions",
        headers=owner_headers,
        json={"username": "readonly_user", "access_level": "read"},
    )
    assert grant.status_code == 200, grant.text

    # Read permission should allow downloading.
    download = client.get(
        f"/documents/{document_id}/download",
        headers=readonly_headers,
    )
    assert download.status_code == 200, download.text

    # But read permission must not allow editing.
    edit = client.put(
        f"/documents/{document_id}",
        headers=readonly_headers,
        json={"name": "Unauthorized Change", "category": "changed"},
    )
    assert edit.status_code == 403, edit.text



def test_admin_can_view_audit_logs():
    admin_token = login_user(
        "test_admin", "TestAdminPass123!"
    )

    response = client.get(
        "/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_viewer_cannot_view_audit_logs():
    assert register_user(
        "audit_viewer", "audit_viewer@example.com"
    ).status_code == 201

    viewer_token = login_user("audit_viewer")

    response = client.get(
        "/admin/audit-logs",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403, response.text




def test_document_upload_is_recorded_in_audit_log():
    assert register_user(
        "audit_upload_owner", "audit_upload_owner@example.com"
    ).status_code == 201

    admin_token = login_user("test_admin", "TestAdminPass123!")
    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    promote = client.post(
        "/admin/users/role",
        headers=admin_headers,
        json={
            "username": "audit_upload_owner",
            "role": "owner",
        },
    )
    assert promote.status_code == 200, promote.text

    owner_token = login_user("audit_upload_owner")
    owner_headers = {
        "Authorization": f"Bearer {owner_token}"
    }

    upload = client.post(
        "/documents/upload",
        headers=owner_headers,
        data={
            "name": "Audit Evidence Test",
            "category": "test",
        },
        files={
            "file": (
                "audit_evidence.txt",
                b"audit test content",
                "text/plain",
            )
        },
    )
    assert upload.status_code == 201, upload.text

    document_id = upload.json()["document_id"]

    logs_response = client.get(
        "/admin/audit-logs",
        headers=admin_headers,
    )
    assert logs_response.status_code == 200, logs_response.text

    matching_logs = [
        log for log in logs_response.json()
        if log["action"] == "upload"
        and log["document_id"] == document_id
    ]

    assert matching_logs, (
        f"No upload audit event found for document {document_id}"
    )



