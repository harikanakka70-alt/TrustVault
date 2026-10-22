
import os
import shutil
import secrets
from pathlib import Path
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from fastapi import (
    FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import models 
from fastapi.middleware.cors import CORSMiddleware


# ---------- Configuration ----------

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TrustVault", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
password_hash = PasswordHash.recommended()
security = HTTPBearer()

SECRET_KEY = os.getenv("TRUSTVAULT_SECRET_KEY", "")
ALGORITHM = "HS256"
TOKEN_MINUTES = 30
MAX_FILE_SIZE = 10 * 1024 * 1024

UPLOAD_DIR = (Path(__file__).resolve().parent / "uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ---------- Request models ----------

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserRoleRequest(BaseModel):
    username: str
    role: str


class PermissionRequest(BaseModel):
    username: str
    access_level: str


class DocumentUpdateRequest(BaseModel):
    name: str
    category: str


# ---------- Common helpers ----------

def record_audit(db, user_id, action, document_id=None, details=None):
    db.add(models.AuditLog(
        user_id=user_id,
        action=action,
        document_id=document_id,
        details=details
    ))
    db.commit()


def require_secret_key():
    if not SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Server authentication is not configured. "
                   "Set TRUSTVAULT_SECRET_KEY before starting the server."
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    require_secret_key()

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def check_document_access(document, user, db, required_level="read"):
    if user.role == "admin" or document.owner_id == user.id:
        return

    permission = db.query(models.Permission).filter(
        models.Permission.document_id == document.id,
        models.Permission.user_id == user.id
    ).first()

    allowed = {
        "read": ("read", "edit"),
        "edit": ("edit",)
    }

    if not permission or permission.access_level not in allowed[required_level]:
        try:
            record_audit(
                db, user.id, "access_denied", document.id,
                f"Required access: {required_level}"
            )
        finally:
            raise HTTPException(status_code=403, detail="Access denied")


def get_document_or_404(document_id, db):
    document = db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


def safe_file_path(document):
    path = Path(document.file_path).resolve()

    if not path.is_relative_to(UPLOAD_DIR):
        raise HTTPException(status_code=404, detail="File not found")

    return path


# ---------- Initial admin setup ----------

@app.on_event("startup")
def create_bootstrap_admin():
    username = os.getenv("TRUSTVAULT_ADMIN_USERNAME")
    email = os.getenv("TRUSTVAULT_ADMIN_EMAIL")
    password = os.getenv("TRUSTVAULT_ADMIN_PASSWORD")

    # Admin creation is optional. Set all three variables to enable it.
    if not (username and email and password):
        return

    if len(password) < 12:
        print("TrustVault: bootstrap admin password must be at least 12 characters")
        return

    db = next(get_db())
    try:
        existing = db.query(models.User).filter(
            or_(
                models.User.username == username,
                models.User.email == email
            )
        ).first()

        if not existing:
            admin = models.User(
                username=username,
                email=email,
                password_hash=password_hash.hash(password),
                role="admin"
            )
            db.add(admin)
            db.commit()
            print("TrustVault: bootstrap admin created")
    finally:
        db.close()


# ---------- Public endpoints ----------

@app.get("/")
def home():
    return {"message": "Welcome to TrustVault"}


@app.get("/health")
def health():
    return {"status": "running"}


@app.post("/register", status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if len(data.password) < 12:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 12 characters"
        )

    existing = db.query(models.User).filter(
        or_(
            models.User.username == data.username,
            models.User.email == data.email
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists"
        )

    user = models.User(
        username=data.username,
        email=data.email,
        password_hash=password_hash.hash(data.password),
        role="viewer"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "user_id": user.id,
        "role": user.role
    }


@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    require_secret_key()

    user = db.query(models.User).filter(
        models.User.username == data.username
    ).first()

    if not user or not password_hash.verify(
        data.password, user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = jwt.encode(
        {
            "sub": str(user.id),
            "exp": datetime.now(timezone.utc)
                   + timedelta(minutes=TOKEN_MINUTES)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    record_audit(db, user.id, "login", details="Successful login")

    return {"access_token": token, "token_type": "bearer"}


# ---------- Admin user management ----------

@app.post("/admin/users/role")
def set_user_role(
    data: UserRoleRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    if data.role not in ("owner", "viewer", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")

    target = db.query(models.User).filter(
        models.User.username == data.username
    ).first()

    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    target.role = data.role
    db.commit()

    record_audit(
        db, user.id, "role_changed",
        details=f"User {target.username} role set to {data.role}"
    )

    return {"message": "User role updated", "role": target.role}


# ---------- Document upload and listing ----------

@app.post("/documents/upload", status_code=201)
def upload_document(
    name: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if user.role not in ("admin", "owner"):
        raise HTTPException(
            status_code=403,
            detail="Only owners and admins can upload documents"
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    safe_name = Path(file.filename).name
    stored_name = f"{secrets.token_hex(16)}_{safe_name}"
    file_path = UPLOAD_DIR / stored_name
    size = 0

    try:
        with file_path.open("wb") as output:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break

                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File exceeds 10 MB limit"
                    )

                output.write(chunk)

        document = models.Document(
            name=name,
            category=category,
            owner_id=user.id,
            file_path=str(file_path)
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        record_audit(
            db, user.id, "upload", document.id,
            f"Uploaded {document.name}"
        )

        return {
            "message": "Document uploaded successfully",
            "document_id": document.id,
            "name": document.name
        }
    except Exception:
        db.rollback()
        if file_path.exists():
            file_path.unlink()
        raise
    finally:
        file.file.close()


@app.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    documents = db.query(models.Document).all()
    results = []

    for doc in documents:
        try:
            check_document_access(doc, user, db, "read")
            results.append({
                "id": doc.id,
                "name": doc.name,
                "category": doc.category,
                "owner_id": doc.owner_id,
                "created_at": doc.created_at
            })
        except HTTPException as exc:
            if exc.status_code != 403:
                raise

    return results


# ---------- Document edit, download and delete ----------

@app.put("/documents/{document_id}")
def update_document(
    document_id: int,
    data: DocumentUpdateRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    document = get_document_or_404(document_id, db)
    check_document_access(document, user, db, "edit")

    document.name = data.name
    document.category = data.category
    db.commit()

    record_audit(
        db, user.id, "edit", document.id,
        f"Updated document metadata: {document.name}"
    )

    return {"message": "Document updated successfully"}


@app.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    document = get_document_or_404(document_id, db)
    check_document_access(document, user, db, "read")

    file_path = safe_file_path(document)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    record_audit(
        db, user.id, "download", document.id,
        f"Downloaded {document.name}"
    )

    return FileResponse(
        path=str(file_path),
        filename=Path(document.file_path).name
    )


@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    document = get_document_or_404(document_id, db)
    check_document_access(document, user, db, "edit")

    if user.role != "admin" and document.owner_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the owner or admin can delete this document"
        )

    file_path = safe_file_path(document)
    name = document.name

    db.query(models.Permission).filter(
        models.Permission.document_id == document.id
    ).delete(synchronize_session=False)

    document_id_for_log = document.id
    db.delete(document)
    db.commit()

    if file_path.is_file():
        file_path.unlink()

    record_audit(
        db, user.id, "delete", document_id_for_log,
        f"Deleted {name}"
    )

    return {"message": "Document deleted successfully"}


# ---------- Document permission management ----------

@app.post("/documents/{document_id}/permissions")
def grant_permission(
    document_id: int,
    data: PermissionRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    document = get_document_or_404(document_id, db)

    if user.role != "admin" and document.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Owner or admin only")

    if data.access_level not in ("read", "edit"):
        raise HTTPException(
            status_code=400,
            detail="Access level must be read or edit"
        )

    target = db.query(models.User).filter(
        models.User.username == data.username
    ).first()

    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if target.id == document.owner_id:
        raise HTTPException(
            status_code=400,
            detail="The owner already has access"
        )

    permission = db.query(models.Permission).filter(
        models.Permission.document_id == document.id,
        models.Permission.user_id == target.id
    ).first()

    if permission:
        permission.access_level = data.access_level
    else:
        db.add(models.Permission(
            document_id=document.id,
            user_id=target.id,
            access_level=data.access_level
        ))

    db.commit()

    record_audit(
        db, user.id, "permission_granted", document.id,
        f"{data.access_level} access granted to {target.username}"
    )

    return {
        "message": "Permission saved",
        "username": target.username,
        "access_level": data.access_level
    }


@app.delete("/documents/{document_id}/permissions/{username}")
def revoke_permission(
    document_id: int,
    username: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    document = get_document_or_404(document_id, db)

    if user.role != "admin" and document.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Owner or admin only")

    target = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    permission = db.query(models.Permission).filter(
        models.Permission.document_id == document.id,
        models.Permission.user_id == target.id
    ).first()

    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    db.delete(permission)
    db.commit()

    record_audit(
        db, user.id, "permission_revoked", document.id,
        f"Access revoked from {target.username}"
    )

    return {"message": "Permission revoked immediately"}


# ---------- Admin document search and audit log ----------


@app.get("/admin/documents")
def admin_search_documents(
    search: str = Query(default=""),
    category: str = Query(default=""),
    owner_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    query = db.query(models.Document)

    if search:
        query = query.filter(models.Document.name.contains(search))

    if category:
        query = query.filter(models.Document.category == category)

    if owner_id is not None:
        query = query.filter(models.Document.owner_id == owner_id)

    return [
        {
            "id": doc.id,
            "name": doc.name,
            "category": doc.category,
            "owner_id": doc.owner_id,
            "created_at": doc.created_at
        }
        for doc in query.order_by(models.Document.id.desc()).all()
    ]


@app.get("/admin/audit-logs")
def admin_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    logs = db.query(models.AuditLog).order_by(
        models.AuditLog.id.desc()
    ).limit(limit).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "document_id": log.document_id,
            "details": log.details,
            "created_at": log.created_at
        }
        for log in logs
    ]