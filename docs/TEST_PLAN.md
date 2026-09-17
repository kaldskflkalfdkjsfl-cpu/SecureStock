# SecureStock Security Test Plan

Each item below maps to at least one automated test in `tests/`. Run everything with:

```bash
pytest --cov=app --cov-report=term-missing
```

Current: **94 automated tests, ~91% line coverage, bandit scan reports
0 issues across `app/`.**

| ID | Test | Expected Result | Automated coverage |
|---|---|---|---|
| SEC-01 | 3 invalid logins | Account locked for 15 min (timezone-safe) | `test_auth.py` |
| SEC-01b | Login while locked | Blocked with generic message | `test_auth.py` |
| SEC-01c | Lockout expiry | Login succeeds after expiry window | `test_auth.py` |
| SEC-02 | Employee visits `/users/` | 403 | `test_rbac.py` |
| SEC-02b | Manager visits `/users/` | 403 | `test_rbac.py` |
| SEC-02c | Employee CRUD on products/customers/users | 403 | `test_rbac.py`, `test_crud.py` |
| SEC-03 | Employee opens another employee's sale | 403 (IDOR) | `test_rbac.py` |
| SEC-03b | Employee sales list shows only own | Filtered list | `test_rbac.py` |
| SEC-04 | XSS string in product name | Script not executed (escaped) | `test_xss_sqli.py` |
| SEC-04b | XSS in search box | Escaped in page | `test_xss_sqli.py` |
| SEC-05 | SQL-like search input | Treated as data (LIKE wildcards escaped) | `test_xss_sqli.py` |
| SEC-06 | POST without CSRF token | CSRF rejection (with token: accepted) | `test_csrf.py` |
| SEC-07 | `../../secret.txt` upload | Path sanitized / rejected | `test_upload.py` |
| SEC-07b | Disallowed extension | Rejected | `test_upload.py` |
| SEC-07c | PNG renamed to `.txt` | Rejected by magic-number check | `test_upload.py` |
| SEC-08 | Sale quantity > stock | Sale rejected, stock unchanged | `test_sales.py` |
| SEC-09 | Exception during sale | Full transaction rollback | `test_sales.py` |
| SEC-10 | Customer phone in DB | Encrypted (Fernet) ciphertext | `test_data_protection.py` |
| SEC-11 | Password in DB | scrypt hash, never plaintext | `test_data_protection.py` |
| SEC-12 | Excessive login requests | 429 rate limit | `test_auth.py` |
| SEC-13 | Unknown email login | Same generic error, timing constant, audited | `test_auth.py`, `test_audit.py` |
| SEC-14 | Failed-login audit rows | `LOGIN_FAILED` / `LOGIN_FAILED_UNKNOWN` recorded | `test_audit.py` |
| SEC-15 | Inventory negative adjustment | Rejected ("cannot become negative") | `test_inventory.py` |
| SEC-16 | Inventory valid adjustment | Applied and audited | `test_inventory.py` |
| SEC-17 | Non-admin visits `/audit/` | 403 | `test_audit.py` |
| SEC-18 | TOTP user logs in | Second factor required; correct code → dashboard | `test_auth.py` |
| SEC-19 | TOTP enrollment | Bad code rejected, valid code enables, code disables | `test_profile.py` |
| SEC-20 | Self-deletion of admin | Rejected with message | `test_crud.py` |
| SEC-21 | Missing resource | Styled 404 page | `test_crud.py` |
| SEC-22 | Change own password | Wrong current → rejected; weak/mismatch → rejected; success → audited + old password invalid | `test_profile.py` |
| SEC-23 | Admin password reset | Sets new password, unlocks account, audited; non-admins get 403 | `test_crud.py` |

## Evidence to capture for the report

- Screenshots of each role's dashboard (Admin / Manager / Employee).
- Screenshot of a 403 authorization rejection.
- Screenshot of account lockout message.
- Screenshot of a successful (manageable) sale transaction.
- Database screenshot showing hash/ciphertext and `AuditLog` rows.
- TOTP enrollment QR screen + login second-factor screen.
- Terminal output of `pytest` (all passing), `ruff check`, and `bandit -r app`
  (0 issues). Reports are also generated into `docs/reports/` by:
  ```bash
  pytest --cov-report=html:docs/reports/htmlcov --cov-report=xml:docs/reports/coverage.xml
  bandit -r app -f html -o docs/reports/bandit.html
  ```
- Final test result table with PASS/FAIL.