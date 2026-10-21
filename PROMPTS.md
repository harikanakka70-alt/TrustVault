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
 
## 11. Permission Revocation Security Test — 21 October 2026

- **Goal:** Verify that revoking a viewer's document permission stops further access.
- **Test added:** `test revoked permission blocks download`
- **Test flow:** Create an owner and viewer, upload a private document, grant read access, verify the viewer can download it, revoke permission, and verify that the viewer is denied afterward.
- **Issue caught and fixed:** The first test run failed with an IndentationError because the new function was indented inside the preceding test. I corrected the function indentation and reran the suite.
- **Verification:** All 10 tests passed, with 2 FastAPI deprecation warnings.
- **Security lesson:** Permission revocation must be enforced by the server on subsequent requests, not merely hidden in the user interface.


## Unauthorized Permission Change Test — 21 October 2026

- **Threat addressed:** T3 — Unauthorized permission changes.
- **Test added:** `test_non_owner_cannot_grant_document_permission`.
- **Test scenario:** A different document owner attempts to grant access to another owner's document.
- **Expected security behavior:** The server rejects the request with HTTP 403 Forbidden.
- **Result:** The test passed.
- **Issue caught and fixed:** The initial test included a hardcoded `owner_id` in the upload form. Reviewing `main.py` showed that the server assigns ownership from the authenticated user (`owner_id=user.id`), so the unnecessary field was removed.
- **Verification:** The full test suite reported 11 passed, 0 failed, and 2 FastAPI deprecation warnings.
- **Lesson:** Security tests should reflect the actual server-side ownership model and test the authorization boundary directly.

### 2026-10-21 — Additional document authorization tests

**Goal:** Strengthen tests for unauthorized document edits and deletions, and for read-only permissions.

**AI assistance:** Used AI to draft three automated security tests.

**Human verification and correction:** Ran the test suite and found that the new tests expected the upload response field `id`. Inspected `main.py` and identified the actual field as `document_id`. Corrected the test references, then fixed a spelling error (`dociment_id`) found in the final test.

**Result:** All 14 tests passed after the corrections.

**Remaining work:** Test upload validation, audit events (including denied attempts), and date-based administrator document search.

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
 
## 11. Permission Revocation Security Test — 21 October 2026

- **Goal:** Verify that revoking a viewer's document permission stops further access.
- **Test added:** `test revoked permission blocks download`
- **Test flow:** Create an owner and viewer, upload a private document, grant read access, verify the viewer can download it, revoke permission, and verify that the viewer is denied afterward.
- **Issue caught and fixed:** The first test run failed with an IndentationError because the new function was indented inside the preceding test. I corrected the function indentation and reran the suite.
- **Verification:** All 10 tests passed, with 2 FastAPI deprecation warnings.
- **Security lesson:** Permission revocation must be enforced by the server on subsequent requests, not merely hidden in the user interface.


## Unauthorized Permission Change Test — 21 October 2026

- **Threat addressed:** T3 — Unauthorized permission changes.
- **Test added:** `test_non_owner_cannot_grant_document_permission`.
- **Test scenario:** A different document owner attempts to grant access to another owner's document.
- **Expected security behavior:** The server rejects the request with HTTP 403 Forbidden.
- **Result:** The test passed.
- **Issue caught and fixed:** The initial test included a hardcoded `owner_id` in the upload form. Reviewing `main.py` showed that the server assigns ownership from the authenticated user (`owner_id=user.id`), so the unnecessary field was removed.
- **Verification:** The full test suite reported 11 passed, 0 failed, and 2 FastAPI deprecation warnings.
- **Lesson:** Security tests should reflect the actual server-side ownership model and test the authorization boundary directly.


## 12. AI-Assisted Security Code Review — 21 October 2026

**Goal:** Review document authorization, permission management, and audit logging before finalizing the threat model.

**Prompt/task:** Review the existing `check_document_access()` helper and document endpoints to identify potential authorization weaknesses. Compare the implementation against the security threats in `THREATS.md`.

**Code inspected:**
- `check_document_access()`
- `GET /documents`
- `PUT /documents/{document_id}`
- `GET /documents/{document_id}/download`
- `DELETE /documents/{document_id}`
- `POST /documents/{document_id}/permissions`
- `DELETE /documents/{document_id}/permissions/{username}`
- `GET /admin/audit-logs`

**Findings:** The reviewed code includes read/edit permission checks, owner/admin restrictions for permission management, an additional owner/admin check for deletion, and audit logging calls for several sensitive operations.

**Security limitations identified:**
- Every protected endpoint must be checked to confirm authorization is consistently enforced.
- Immediate permission revocation needs to be verified through subsequent requests.
- Audit-event completeness and failure handling require dedicated tests.
- File-upload validation and safe file-path handling need further review.

**Correction to approach:** Do not assume that a security control is effective solely because a helper function or audit call exists. Map each threat to the relevant code and verify it with a reproducible test.

**Verification status:** Code-review observations recorded. No new automated test result is claimed by this section.

**Next action:** Compare the actual test functions with the threats, run the missing security tests, and record their real outputs and any fixes.



