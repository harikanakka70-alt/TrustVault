# TrustVault — AI Usage and Correction Log

## Purpose

This file documents how AI assistance was used during the development of TrustVault, the issues identified, the corrections made, and the evidence used to verify the changes.

AI-generated suggestions were treated as proposals rather than automatically trusted solutions. I checked relevant code, API responses, test results, and error messages before accepting corrections.

This log distinguishes between:
- **Observed:** directly seen in code, terminal output, API responses, or test results.
- **Verified:** checked through a recorded test or reproducible manual action.
- **Remaining:** not yet fully verified or completed.

## 1. Python Environment and Backend Setup

**Task:** Set up the Python environment and run the FastAPI backend on Windows.

**Issues encountered:**
- The virtual environment was created in the project root while the backend code was inside the `backend` directory.
- Activating the environment was affected by PowerShell execution-policy restrictions.
- Required packages were initially missing, including SQLAlchemy and Uvicorn.

**Correction and verification:**
- Used the project virtual environment's Python executable directly when activation was inconvenient.
- Installed the required backend dependencies.
- Started the FastAPI application and accessed the local Swagger UI at `http://127.0.0.1:8000/docs`.

**Lesson learned:** Python commands must use the intended virtual environment, and the server must run from the correct project directory with the required dependencies installed.

## 2. SQLAlchemy Model Declaration Error

**Task:** Define the database models for users, documents, and permissions.

**Issue encountered:** SQLAlchemy raised an error because a model used `_tablename_` instead of the required `__tablename__` attribute.

**Correction:** Changed the model declarations to use `__tablename__` and checked that the models could be loaded by the application.

**Security relevance:** Incorrect model definitions can prevent the application from starting and can interfere with database-backed authorization features.

## 3. Authentication and Role-Based Access Control

**Task:** Implement authentication and distinguish administrators, document owners, and viewers.

**Implementation and verification work:**
- Added registration and login endpoints.
- Used password hashing rather than storing plaintext passwords.
- Implemented bearer-token authentication with JWT expiration.
- Restricted user-role changes to administrators.
- Restricted document uploads to administrators and owners.
- Added automated tests for forged tokens, expired tokens, short passwords, and unauthorized role changes.

**Observed results:** Automated tests confirmed that a viewer was denied access to role-changing and document-upload operations, and that forged and expired tokens were rejected.

**Security considerations:** A successful login alone does not prove that every protected endpoint correctly enforces authentication and authorization. Missing-token behavior, invalid credentials, password-hash verification, and token-claim validation should be checked against the current implementation and test suite.

**Secret handling:** The JWT signing key must be supplied through the `TRUSTVAULT_SECRET_KEY` environment variable. A real secret must not be committed to the repository or included in this log.

## 4. Document Ownership and Insecure Direct Object Reference (IDOR)

**Threat:** A user may change a document ID in a URL or API request to access another user's confidential document.

**Task:** Test document access across different users.

**Issues encountered:**
- An initial upload attempt used a viewer account and was correctly rejected because viewers cannot upload documents.
- The test setup needed an appropriately authorized owner account.
- The initial test expected the wrong response status and used `id` instead of the actual response field `document_id`.

**Correction:** Updated the test to use the appropriate authorized test account and the actual API response field and status code.

**Verification:** Added or corrected automated tests for unauthorized downloads and document-access restrictions. The latest recorded automated run completed with 17 passed, 0 failed, and 2 warnings.

**Security relevance:** Authorization must be checked on the server for each requested document. Hiding document IDs or relying on the user interface is not sufficient protection.

## 5. Syntax Errors and Test Corrections

**Task:** Correct Python and test-file errors encountered during development.

**Issues encountered:** Incorrect indentation, misplaced Markdown code fences, and test-code mistakes caused errors during execution.

**Correction:** Checked the relevant file structure, corrected indentation and syntax, and reran the tests after changes.

**Lesson learned:** Error messages should be used to identify the failing location. After correcting code, rerun the relevant test rather than assuming the change worked.

Historical test counts below describe earlier development stages. They should not be interpreted as the current result.

## 6. Git and Version Control

**Task:** Track project changes in Git and push work to GitHub.

**Observed evidence:** A commit with the message `Fix document access security tests` was recorded as commit `3033954`. Later changes were also pushed to the repository's `master` branch.

**Correction and practice:**
- Commit meaningful changes during development.
- Review the staged changes before committing.
- Check `.gitignore` and avoid committing `.env` files, signing keys, passwords, uploaded confidential documents, and other sensitive data.
- Keep the repository private when required by the assignment instructions.

**Lesson learned:** Commit history provides evidence of development progress and corrections. A successful push does not, by itself, prove that the application is secure or deployed.

## 7. Threat Modeling and Security Review

The following threats were considered during development:

| Threat | Relevant defense or verification |
|---|---|
| IDOR / cross-user document access | Server-side document ownership and permission checks; unauthorized-access tests |
| Privilege escalation | Role restrictions and tests for viewer access to administrative operations |
| Forged or expired tokens | JWT validation and authentication tests |
| Unauthorized upload | Role-based upload restriction and automated test |
| Permission abuse | Ownership checks for permission changes |
| Revoked access remaining usable | Test that a revoked viewer can no longer download the document |
| Read-only permission used to edit | Automated test for edit denial |
| Unauthorized edit or deletion | Automated tests for non-owner edit and delete attempts |
| Unsafe filename or path manipulation | Filename handling and safe-path checks in the implementation |
| Oversized upload | File-size limit in the upload implementation |
| Missing audit evidence | Tests for selected audit events and administrator-only audit-log access |
| Exposure of signing keys | Environment-based secret configuration and repository hygiene |

**Important limitation:** These defenses cover selected threats, not every possible attack. A threat should be marked fully verified only when the relevant implementation and a reproducible test or manual check provide evidence.

## 8. Latest Automated Test Evidence

**Test date:** 21 October 2026

**Observed result:** The latest recorded automated test run completed with **17 passed, 0 failed, and 2 warnings**.

The two warnings concerned FastAPI's deprecated `on_event` startup mechanism. They were warnings, not test failures.

The recorded test suite covered:

1. Health endpoint.
2. Home endpoint.
3. Rejection of short passwords.
4. Rejection of forged tokens.
5. Denial of role changes by viewers.
6. Denial of document uploads by viewers.
7. Rejection of expired tokens.
8. Denial of downloads without permission.
9. Denial of downloads for another user's document.
10. Denial of downloads after permission revocation.
11. Denial of permission grants by non-owners.
12. Denial of unauthorized document edits.
13. Denial of unauthorized document deletions.
14. Denial of editing with read-only permission.
15. Administrator access to audit logs.
16. Denial of audit-log access to viewers.
17. Recording of document uploads in the audit log.

**Interpretation:** These results provide evidence for the listed scenarios. They do not establish that every assignment requirement, edge case, or security threat has been fully tested.

## 9. Permission Revocation

**Threat:** A viewer may continue accessing a document after the owner revokes permission.

**Task:** Verify that revoked access is denied.

**Test scenario:**
1. Create a document as an authorized owner.
2. Grant a viewer read permission.
3. Confirm that the viewer can download the permitted document.
4. Revoke the viewer's permission.
5. Attempt the download again using the viewer's credentials.
6. Confirm that the request is denied.

**Observed result:** The automated test `test_revoked_permission_blocks_download` passed in the latest recorded test run.

**Security relevance:** Revocation must be enforced by the backend on subsequent requests, not just reflected in the user interface.

## 10. Unauthorized Permission Changes

**Threat:** A user who does not own a document may try to grant another user access.

**Task:** Test authorization for permission changes.

**Issue encountered:** An initial test supplied an `owner_id` value even though the server determines ownership from the authenticated user.

**Correction:** Updated the test setup to use the authenticated owner and rely on the server-side ownership model.

**Observed result:** The automated test `test_non_owner_cannot_grant_document_permission` passed in the latest recorded test run.

**Security relevance:** The backend must not trust a client-supplied owner ID to establish authority over a document.

## 11. Additional Document Authorization Tests

**Task:** Extend coverage for editing, deleting, and read-only access.

**Corrections made:**
- Corrected the upload-response field used by the tests.
- Corrected a misspelled variable in the test code.
- Checked that a non-owner cannot edit another user's document.
- Checked that a non-owner cannot delete another user's document.
- Checked that read permission alone does not allow editing.

**Observed result:** The three relevant authorization tests were included in the latest recorded test run, which completed with 17 passed and 0 failed.

**Security relevance:** Read access and edit access are different privileges. The backend must enforce the required permission level for each operation.

## 12. AI-Assisted Security Code Review — 21 October 2026

**Task:** Review the document-authorization and audit-related code paths for potential security weaknesses.

**Areas reviewed:**
- The document-access helper.
- Document listing and filtering.
- Document updates and downloads.
- Document deletion.
- Permission granting and revocation.
- Administrator audit-log access.

**Review approach:** AI-assisted review was used to identify areas requiring attention. Findings were treated as items to inspect, not as proof that a vulnerability existed or had been fixed.

**Verification approach:** Relevant implementation details and existing automated tests were checked. The latest recorded suite passed, but it does not cover every possible attack or every branch of every endpoint.

**Remaining considerations:** Continue checking denied-access audit events, permission edge cases, file-path handling, upload failure cleanup, persistence, and the remaining assignment requirements. Do not claim that a check passed unless it was actually performed.

## 13. Lessons Learned

- AI-generated code and explanations must be checked against the actual application.
- Error messages, API responses, and automated tests provide concrete evidence for corrections.
- Authorization must be enforced by the backend for every protected operation.
- Document ownership must come from authenticated server-side identity, not a trusted client-supplied identifier.
- Read and edit permissions must be distinguished.
- Permission revocation must affect subsequent access attempts.
- Secrets must be managed outside committed source code.
- Passing tests provide evidence for the tested scenarios, not a guarantee of complete security.
- Git commits document changes but do not replace testing or security review.

## 14. Remaining Work and Verification Limits

The following items should be marked complete only after they have been checked against the current implementation and assignment requirements:

1. Verify that every required role and document-management operation works as specified.
2. Review permission granting, revocation, and immediate denial after revocation; retain the existing automated tests and investigate any remaining untested cases.
3. Review authorization for document edits, deletions, and permission changes, including edge cases not covered by current tests.
4. Verify file-size limits, unsafe-filename handling, and path containment. Do not claim that file-extension restrictions are implemented unless the code enforces them and the assignment requires them.
5. Check audit coverage for uploads, downloads, edits, deletions, permission changes, and denied access attempts.
6. Verify administrator search and filtering by the required fields, including date filters.
7. Check database and uploaded-file persistence across application restarts.
8. Verify that sensitive values and confidential uploaded files are excluded from Git commits.
9. Verify deployment and test the deployed application independently if deployment is required.
10. Review the threat model against the actual code and automated tests, and record any gaps honestly.

**Final status:** The latest recorded automated run provides evidence that 17 tests passed with no failures. Deployment status, complete requirement coverage, and complete threat coverage must be assessed separately.

