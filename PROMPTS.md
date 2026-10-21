\# TrustVault — AI Usage and Correction Log



\## Purpose



This file documents how AI assistance was used while developing TrustVault, including problems encountered, corrections made, and security decisions that require verification.



\## 1. Backend Setup and Environment



\*\*Task:\*\* Set up the Python environment and run the FastAPI backend.



\*\*AI assistance:\*\* Used step-by-step guidance for Python virtual environments, dependency installation, and starting Uvicorn.



\*\*Problem encountered:\*\* The virtual environment was stored in the project root rather than inside the backend folder. PowerShell also blocked activation because of its script execution policy.



\*\*Correction:\*\* Located the existing environment and ran its Python executable directly to start Uvicorn, avoiding the need to change the PowerShell execution policy.



\*\*Evidence:\*\* The server reported that application startup was complete.



\## 2. Database Models



\*\*Task:\*\* Define SQLAlchemy models for users, documents, and permissions.



\*\*Problem encountered:\*\* An earlier model definition used an incorrect table-name attribute, causing a SQLAlchemy model configuration error.



\*\*Correction:\*\* Identified the need to use SQLAlchemy's correct `\_\_tablename\_\_` attribute and verify the model definitions.



\*\*Remaining verification:\*\* Confirm that all required tables and relationships exist and that permissions are enforced correctly.



\## 3. Authentication and Authorization



\*\*Task:\*\* Implement registration, login, JWT authentication, and role-based access.



\*\*AI assistance:\*\* Used guidance to structure authentication and protected API endpoints.



\*\*Security considerations:\*\* Passwords must be hashed, JWT signing secrets must be configured securely, and user roles must not be trusted when supplied by an unauthorized client.



\*\*Remaining verification:\*\* Test missing, invalid, and expired tokens; unauthorized role changes; and access to documents owned by other users.



\## 4. Document Permissions



\*\*Task:\*\* Support document upload, download, editing, deletion, and permission management.



\*\*Security concern:\*\* Changing a document ID must not allow a user to access another user's document.



\*\*Required correction and verification:\*\* Check authorization on every protected operation. Test that access is denied when the user lacks permission and that revoked permissions stop working immediately.



\*\*Evidence to add:\*\* Record actual test commands, expected outcomes, and observed results after running the security tests.



\## 5. Server and API Troubleshooting



\*\*Task:\*\* Diagnose server connection and routing issues.



\*\*Problem encountered:\*\* The health endpoint initially could not be reached because the server was not running in the active session. Multiple Python processes had also been observed on port 8000 during earlier troubleshooting.



\*\*Correction:\*\* Restarted Uvicorn using the existing virtual environment and confirmed that the application started successfully.



\*\*Remaining verification:\*\* Confirm health checks, API routes, and authentication behavior against the currently running application.



\## 6. Git and GitHub



\*\*Task:\*\* Track project changes and preserve development history.



\*\*Problems encountered:\*\* Git initially lacked a configured author identity, and the local project had not yet been connected to a remote repository.



\*\*Correction:\*\* Configured the Git author identity, initialized the repository, added a `.gitignore`, committed the backend, created a private GitHub repository, and pushed commits.



\*\*Security consideration:\*\* The database, uploaded documents, and virtual environment should not be committed. Review repository contents before every push.



\## 7. Threat Modeling



\*\*Task:\*\* Identify threats to confidential documents and define verification steps in `THREATS.md`.



\*\*AI assistance:\*\* Used AI to organize threats involving unauthorized document access, privilege escalation, authentication failures, malicious uploads, permission revocation, audit logs, and data loss.



\*\*Critical limitation:\*\* A written mitigation does not prove that the application implements it. Each threat must be tested against the actual code, and any failed test must be documented and fixed.



\## 8. Lessons Learned



\- AI-generated code and security recommendations require independent verification.

\- Successful application startup does not establish that the application is secure.

\- Authorization must be enforced by the backend, not just the user interface.

\- Secrets and confidential files must be excluded from source control.

\- Security tests must cover both authorized and unauthorized actions.

\- Unverified functionality must not be presented as completed.



\## 9. Test Evidence and Outstanding Work



This document is a working log. Add dated entries describing actual prompts, AI mistakes, corrections, commands, and test results as development continues.



Do not claim that a test passed unless it has been executed and its result observed.



Outstanding work includes verifying all assignment requirements, executing security tests, reviewing file-upload validation and audit coverage, configuring persistent cloud storage, deploying the application, and testing the deployed service.

