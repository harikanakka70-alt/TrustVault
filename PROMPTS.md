# TrustVault — AI Usage and Correction Log

## Purpose

This log records how AI assistance was used to develop TrustVault, including tasks, errors encountered, corrections, verification evidence, and remaining security work. The entries distinguish observed results from features that still need testing.

## 1. Python Environment and Backend Setup

**Task:** Set up the Python environment, install dependencies, and run the FastAPI backend.

**AI assistance:** Requested step-by-step guidance for virtual environments, dependency installation, and starting the server.

**Problem encountered:** The virtual environment was located in the project root rather than inside the backend folder. PowerShell activation and missing dependencies also caused setup difficulties.

**Correction:** Located the existing environment and used its Python executable directly. Installed the required packages and used the existing environment to run commands.

**Evidence:** The backend started successfully, and the automated test suite was later run using the same virtual environment.

**Lesson:** Understand the active Python environment before installing packages or diagnosing import errors.

## 2. SQLAlchemy Model Configuration

**Task:** Define database models for users, documents, and permissions.

**Problem encountered:** An earlier model definition used `_tablename_` instead of SQLAlchemy's required `__tablename__` attribute, resulting in a model configuration error.

**Correction:** Identified the incorrect attribute and corrected the table-name declaration.

**Verification still required:** Review the database schema, relationships, constraints, and permission enforcement against the assignment requirements.

**Lesson:** An apparently small naming error can prevent the application from initializing. Model changes should be verified by running the application and relevant tests.

## 3. Authentication and Authorization

**Task:** Implement registration, login, JWT authentication, and role-based access.

**AI assistance:** Used guided troubleshooting to understand protected endpoints and test authentication and authorization behavior.

**Security issue considered:** New accounts default to the viewer role. A viewer must not be able to assign themselves an owner or admin role or upload documents without authorization.

**Correction and evidence:** Automated tests now verify that a viewer's attempt to change a role is rejected and that a viewer's upload attempt is rejected. The test suite also checks invalid and expired authentication tokens.

**Observed result:** These tests passed in the test run recorded on 21 October 2026.

**Remaining verification:** Test missing tokens, invalid login credentials, password hashing, token claims, and additional authorization edge cases.

## 4. Document Access and IDOR Testing

**Task:** Verify that a user cannot access another user's private document by changing its document ID.

**Initial problem:** The first test attempted to upload a document as a newly registered viewer. The API correctly returned `403 Forbidden`, because only owners and admins can upload documents.

**Correction:** Configured a test-only admin account, promoted the test document owner through the admin role-management endpoint, and retried the upload with the owner's token.

**Second problem:** The upload endpoint returned `201 Created`, while the test expected `200`. The response used the field `document_id`, not `id`.

**Correction:** Updated the test to expect `201` and read the returned `document_id`.

**Observed result:** The revised test passed. It creates a private document and checks that a different viewer cannot download it. The suite also checks a request for a nonexistent document ID.

**Limitation:** These tests cover specific download scenarios. They do not yet prove that every document read, edit, delete, and permission-management endpoint prevents IDOR.

**Lesson:** Tests must reflect the actual API contract, and successful upload alone does not prove that document authorization is secure.

## 5. Test Syntax and Test Setup Corrections

**Task:** Maintain a reliable automated security test suite.

**Problems encountered:** Copying code into the Python file introduced Markdown code fences and incorrect indentation. These caused syntax and test-collection errors.

**Correction:** Removed the Markdown markers, corrected the indentation, and reran pytest.

**Observed result:** The final recorded run completed with **9 passed, 0 failed, and 2 warnings**. The warnings concerned FastAPI's deprecated `on_event` startup mechanism; they were not test failures.

**Lesson:** Code copied from documentation must be placed into source files without Markdown formatting. A test suite must be executed after edits rather than assumed to be valid.

## 6. Git and GitHub

**Task:** Preserve the project history and commit development progress.

**AI assistance:** Used step-by-step Git guidance to check status, stage changes, commit, and push to the remote repository.

**Observed result:** Commit `3033954` (`Fix document access security tests`) was successfully pushed to the `master` branch on 21 October 2026.

**Security consideration:** Keep the repository private as required by the assignment instructions. Review `.gitignore` and repository contents to ensure that secrets, local databases, uploaded confidential files, and virtual-environment files are not committed.

## 7. Threat Modeling

**Task:** Create `THREATS.md` to identify realistic risks to confidential documents and describe mitigations and verification steps.

**AI assistance:** Used AI to organize threats involving IDOR, privilege escalation, unauthorized permission changes, revoked access, password exposure, forged or expired tokens, malicious uploads, audit-log gaps, sensitive-data leakage, and data loss.

**Critical limitation:** A mitigation written in documentation is not proof that it is implemented. Threats must be linked to actual tests, code review, or operational evidence.

**Correction:** Added a verification-status section to distinguish partially tested threats from those without dedicated tests.

**Remaining work:** Add and execute tests for permission revocation, unauthorized permission changes, file validation, audit events, sensitive-data leakage, and persistence.

## 8. Current Automated Test Evidence

**Date:** 21 October 2026

**Command used:**

`D:\model\TrustVault\.venv\Scripts\python.exe -m pytest test_main.py -v`

**Observed result:** 9 passed, 0 failed, 2 warnings.

The passing tests cover:

- Health endpoint.
- Home endpoint.
- Short-password rejection.
- Forged-token rejection.
- Viewer role-change rejection.
- Viewer upload rejection.
- Expired-token rejection.
- Rejection of a download request for a nonexistent document.
- Rejection of another viewer's attempt to download a private document.

**Scope limitation:** Passing these nine tests does not establish that all assignment requirements or all threats have been verified.

## 9. Lessons Learned

- AI-generated code and security recommendations must be independently checked.
- Authentication and authorization are different: a logged-in user is not automatically authorized to access every document.
- Tests must check both permitted and denied operations.
- API status codes and response fields should be verified against actual responses.
- Secrets and confidential data must not be committed to source control.
- Test results should be recorded only after running the tests.
- Unfinished functionality and unresolved security risks must be reported honestly.

## 10. Outstanding Work

The following work remains to be completed and verified before submission:

1. Map every assignment requirement to an implemented feature and a verification test.
2. Test permission granting, permission revocation, and immediate denial after revocation.
3. Test unauthorized document edits, deletions, and permission changes.
4. Test allowed file types, file-size limits, and unsafe filenames.
5. Verify audit events for sensitive operations and denied attempts.
6. Review password storage, API errors, logs, and repository contents for sensitive-data exposure.
7. Verify database and document persistence and recovery.
8. Deploy the application and test the deployed service, including authorization, in a separate browser session.
9. Update this log with actual results, including failures and their fixes.

Do not mark an item complete until its implementation and evidence have been checked.
