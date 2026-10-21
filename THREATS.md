\# TrustVault Security Threat Model



\## 1. Purpose



TrustVault stores confidential documents such as salary letters, customer contracts, and audit reports. This document identifies threats to confidentiality, integrity, and availability.



\## 2. Assets to Protect



\- User accounts, passwords, and authentication tokens.

\- Confidential documents and their metadata.

\- Document ownership and access permissions.

\- Audit logs containing security-relevant events.

\- Application configuration and secret keys.



\## 3. Threats and Mitigations



\### T1: Unauthorized Document Access (IDOR)



\*\*Threat:\*\* An authenticated user changes a document ID in a URL or API request to access another user's document.



\*\*Mitigation:\*\* Check document ownership and explicit permissions on every document read, download, edit, and delete operation. Never rely on unpredictable IDs alone.



\*\*Verification:\*\* Create two users with different document permissions. Attempt to access the other user's document by changing its ID and verify access is denied.



\### T2: Privilege Escalation



\*\*Threat:\*\* A viewer attempts to register or modify their account as an administrator or document owner.



\*\*Mitigation:\*\* Validate roles on the server. Restrict role changes to authorized administrators and never trust a role supplied by an ordinary user.



\*\*Verification:\*\* Attempt unauthorized role assignment and verify the request is rejected.



\### T3: Unauthorized Permission Changes



\*\*Threat:\*\* A user grants access to a document they do not own or removes another user's permissions.



\*\*Mitigation:\*\* Authorize permission creation, modification, and revocation on the server. Only authorized users may change document permissions.



\*\*Verification:\*\* Attempt to change permissions for a document owned by another user and verify the operation is denied.



\### T4: Revoked Access Still Works



\*\*Threat:\*\* A user continues accessing a document after the owner revokes their permission.



\*\*Mitigation:\*\* Check current permissions on every protected request instead of relying on stale authorization decisions or cached access.



\*\*Verification:\*\* Grant access, verify the user can access the document, revoke access, and immediately retry the same request.



\### T5: Password Exposure or Account Compromise



\*\*Threat:\*\* Weak password handling or leaked credentials allow an attacker to impersonate a user.



\*\*Mitigation:\*\* Store password hashes rather than plaintext passwords, use secure password verification, protect authentication secrets, and avoid logging passwords or tokens.



\*\*Verification:\*\* Inspect stored user records to confirm plaintext passwords are not present. Test invalid login credentials.



\### T6: Forged or Expired Authentication Tokens



\*\*Threat:\*\* An attacker modifies a token, uses an expired token, or accesses protected routes without valid authentication.



\*\*Mitigation:\*\* Validate token signatures, expiry, and required claims. Reject missing, invalid, and expired tokens.



\*\*Verification:\*\* Test protected endpoints without a token, with an invalid token, and with an expired token.



\### T7: Malicious or Oversized File Uploads



\*\*Threat:\*\* An attacker uploads an executable, a misleading file type, or a file large enough to exhaust server resources.



\*\*Mitigation:\*\* Validate file size, permitted file types, filenames, and metadata. Generate safe storage names and prevent uploaded content from being executed.



\*\*Verification:\*\* Test disallowed file types, oversized files, and filenames containing path traversal sequences.



\### T8: Audit Log Tampering or Missing Events



\*\*Threat:\*\* A user performs a sensitive operation without a corresponding audit record, or unauthorized users modify audit records.



\*\*Mitigation:\*\* Record security-relevant events, including uploads, downloads, changes, deletions, permission changes, and denied access attempts. Restrict audit-log access and prevent ordinary users from altering logs.



\*\*Verification:\*\* Exercise sensitive operations and denied requests, then confirm the expected events are recorded and unauthorized log access is denied.



\### T9: Sensitive Data Leakage



\*\*Threat:\*\* API responses, error messages, logs, or publicly accessible files expose confidential documents or secrets.



\*\*Mitigation:\*\* Return only authorized data, use generic error responses where appropriate, keep secrets out of source control, and store files outside publicly served directories.



\*\*Verification:\*\* Inspect unauthorized responses, error messages, logs, and repository contents for sensitive data.



\### T10: Database or File Loss



\*\*Threat:\*\* A restart, deployment, or accidental deletion causes loss of documents, permissions, or audit history.



\*\*Mitigation:\*\* Use persistent storage, controlled database migrations, backups, and tested recovery procedures. Do not assume an ephemeral hosting filesystem preserves files.



\*\*Verification:\*\* Confirm uploaded files and database records survive a planned restart or deployment according to the chosen hosting configuration.



\## 4. Security Testing Principles



\- Test both permitted and denied actions.

\- Use separate accounts with different roles and document permissions.

\- Verify authorization on every relevant endpoint, not only in the user interface.

\- Confirm that security failures do not expose confidential data.

\- Keep test evidence and document any discovered defects and fixes.



\## 5. Limitations and Evidence



A mitigation is not considered verified merely because it is documented. Each verification step must be executed against the implementation, and its actual result must be recorded. Any unresolved threat must be reported honestly before submission.



\## 6. Current Verification Status



\*\*Last test run:\*\* 21 October 2026  

\*\*Automated test result:\*\* 9 passed, 0 failed.



The following status reflects the automated tests currently implemented in `backend/test\_main.py`. A passing test verifies only the specific behavior it exercises; it does not prove that an entire threat category is fully mitigated.



| Threat | Current evidence | Status |

|---|---|---|

| T1: IDOR | Test checks that a viewer cannot download another user's private document. | Partially tested |

| T2: Privilege escalation | Tests reject a viewer's attempt to change a role and upload a document. | Partially tested |

| T3: Unauthorized permission changes | No dedicated cross-owner permission-change test yet. | Not yet tested |

| T4: Revoked access | No dedicated grant, revoke, and retry test yet. | Not yet tested |

| T5: Password exposure or account compromise | Short-password rejection is tested. Password-storage inspection and explicit invalid-login testing remain outstanding. | Partially tested |

| T6: Forged or expired tokens | Invalid-token and expired-token rejection are tested. Missing-token behavior and other token claims need additional verification. | Partially tested |

| T7: Malicious or oversized uploads | No dedicated file-type, file-size, or path-traversal tests yet. | Not yet tested |

| T8: Audit log tampering or missing events | No dedicated audit-event completeness or tampering tests yet. | Not yet tested |

| T9: Sensitive data leakage | No systematic response, log, storage, or repository leakage review has been completed. | Not yet tested |

| T10: Database or file loss | Persistence and recovery have not yet been verified through a restart or recovery test. | Not yet tested |



\### Next Verification Work



1\. Add tests for permission changes, immediate permission revocation, and unauthorized document operations.

2\. Add upload validation tests for prohibited file types, oversized files, and unsafe filenames.

3\. Verify that audit logs record sensitive operations and denied attempts.

4\. Inspect password storage, authentication responses, and error responses for sensitive-data exposure.

5\. Verify persistence and recovery using the actual database and file-storage configuration.

6\. Re-run the test suite after each change, record the actual results, and update this section only when new evidence supports a status change.



A threat marked "Not yet tested" is not necessarily exploitable; it means the current test evidence is insufficient to claim that the threat has been addressed.



