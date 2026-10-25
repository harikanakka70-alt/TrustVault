# TrustVault — Secure Document Management System

## 1. Project Overview

TrustVault is a secure document management web application designed to protect confidential files such as salary letters, customer contracts, and audit reports.

The application provides authentication, role-based access control, document management, fine-grained permissions, and audit logging. Users can access only the documents and operations authorized for their roles and individual permissions.

**Important:** This is an existing project. Improve and extend the current implementation instead of recreating the application from scratch.

## 2. Technology Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- JWT-based authentication
- Password hashing
- Relational database configured by the backend

### Frontend
- React
- JavaScript
- HTML and CSS
- npm-based build and dependency management
- API integration with the FastAPI backend

### Deployment
- GitHub for source control
- Render for hosting the frontend and backend

Use the dependencies and configuration already present in the repository. Do not replace the existing technology stack without a clear reason.

## 3. User Roles

### Admin
- View and manage users.
- Assign permitted user roles.
- Search documents using relevant metadata.
- View audit logs.
- Access administrative dashboards and document-management functions according to the authorization policy.

### Document Owner
- Upload documents.
- Organize and search documents.
- View documents they own or are authorized to access.
- Edit or delete documents they own, subject to the authorization policy.
- Grant and revoke document permissions for named users.
- Review the permissions associated with their documents.

### Viewer
- View and download documents only when authorized.
- Must not edit or delete documents unless an explicitly authorized permission and policy allow it.
- Must never gain access by changing a document ID or URL.

## 4. Core Functional Requirements

1. Authentication with secure password hashing and JWT-based sessions.
2. Role-based authorization for Admin, Owner, and Viewer.
3. Document upload with file validation and metadata.
4. Document listing, organization, search, and filtering.
5. Document details, editing, and deletion with server-side authorization.
6. Per-document permissions for named users.
7. Permission granting and revocation by authorized document owners.
8. Immediate enforcement of revoked permissions on subsequent requests.
9. Audit logging for uploads, downloads, edits, deletions, permission changes, and denied access attempts.
10. Administrative document search and audit-log visibility.

Treat these requirements as acceptance criteria. Verify the existing implementation before claiming that any feature is complete.

## 5. Security Requirements

Security is a primary requirement, not an optional enhancement.

- Never trust a user ID, owner ID, role, or permission supplied by the frontend without server-side verification.
- Enforce authentication and authorization on every protected backend endpoint.
- Prevent insecure direct object reference (IDOR) attacks.
- Verify document ownership or explicit permission before reading, downloading, editing, or deleting a document.
- Validate uploaded file names, file types, file sizes, and metadata.
- Prevent path traversal and unauthorized filesystem access.
- Store passwords using an appropriate password-hashing algorithm.
- Load the JWT signing secret from environment variables. Never hardcode production secrets.
- Configure CORS to allow only the intended frontend origins in production.
- Never expose secret keys, password hashes, or sensitive file contents in API responses or logs.
- Record denied access attempts without logging passwords, bearer tokens, or other secrets.
- Ensure revoked permissions are checked against current server-side data.
- Validate all input and handle errors without exposing internal stack traces.
- Use secure production configuration for database connections, file storage, and authentication.

## 6. Frontend Requirements

Improve the existing React frontend to provide a professional, responsive interface.

The application should include, where supported by the backend:

- Login and registration.
- Role-aware navigation and dashboards.
- Document listing and search.
- Document upload with metadata.
- Document viewing and downloading.
- Document editing and deletion controls.
- Permission management for document owners.
- Administrative user management.
- Administrative audit-log viewing.
- Loading indicators, success messages, and useful error messages.
- Responsive layouts for desktop and mobile screens.
- Proper handling of expired tokens and unauthorized API responses.

Frontend controls are not a security boundary. All permissions must also be enforced by the backend.

## 7. Backend API

Inspect the existing FastAPI routes before adding or modifying endpoints. The existing API includes routes for:

- `/`
- `/health`
- `/register`
- `/login`
- `/admin/users/role`
- `/documents/upload`
- `/documents`
- `/documents/{document_id}`
- `/documents/{document_id}/download`
- `/documents/{document_id}/permissions`
- `/documents/{document_id}/permissions/{username}`
- `/admin/documents`
- `/admin/audit-logs`

Confirm the actual HTTP methods, request schemas, response schemas, and authorization rules from the source code.

Keep the frontend API calls consistent with the backend. Avoid duplicate endpoints or breaking existing API contracts.

## 8. Instructions for GitHub Copilot

Before making changes:

1. Inspect the root directory and the `backend` and `frontend` folders.
2. Read the existing source files, README, dependency files, environment configuration, and tests.
3. Identify which features already work and which are incomplete.
4. Explain the proposed changes and the files that need modification.

When implementing changes:

- Preserve the existing architecture wherever practical.
- Do not recreate the frontend or backend unnecessarily.
- Do not overwrite working code without understanding its purpose.
- Avoid introducing unnecessary dependencies.
- Keep secrets and local environment files out of Git.
- Update documentation when behavior changes.
- Add or update tests for every security-sensitive change.
- Do not claim tests pass unless they have actually been run.
- Do not claim deployment succeeds unless the deployed service has been verified.

## 9. Testing Requirements

Test at least the following:

- Successful and unsuccessful login.
- Access to protected endpoints without a token.
- Role-based restrictions for Admin, Owner, and Viewer.
- Access to another user's document by changing the document ID.
- Unauthorized document downloads.
- Unauthorized document edits and deletions.
- Granting and revoking permissions.
- Immediate denial of access after permission revocation.
- Invalid file types and oversized uploads.
- Audit-log entries for successful and denied operations.
- Expired or invalid JWT tokens.
- Frontend API connectivity and production configuration.

Include both positive and negative tests. A security test should demonstrate that unauthorized access is rejected, not merely that an endpoint responds.

## 10. Deployment Requirements

The project is maintained in GitHub and deployed on Render.

- Preserve the existing repository structure.
- Verify backend and frontend build and start commands.
- Configure production environment variables through Render.
- Ensure the frontend uses the deployed backend API URL rather than localhost.
- Configure CORS for the actual deployed frontend origin.
- Check database persistence and uploaded-file storage across deployments.
- Verify health checks, API connectivity, authentication, and document permissions after deployment.
- Never commit production credentials or secrets.

## 11. Documentation

Maintain the following project documentation:

- `README.md`: project overview, setup, architecture, configuration, API, and deployment.
- `THREATS.md`: security threats, mitigations, and evidence from tests.
- `PROMPTS.md`: AI-assisted development history, incorrect suggestions, corrections, and verification.

Keep documentation accurate and distinguish implemented, tested, and pending features.

## 12. Final Goal

Deliver a functional, secure, maintainable document-management application that satisfies the original requirements.

Start by auditing the existing repository. Identify gaps, propose the smallest safe changes, implement them incrementally, run tests, and report the actual results.

Do not replace the entire project simply to add features.
