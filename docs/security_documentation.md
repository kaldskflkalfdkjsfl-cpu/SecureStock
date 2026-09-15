# SecureStock — Secure Programming Practical Project Documentation

## Part One: Project Documentation

### 1. Security Requirements Engineering (SRE)

#### Assets — exactly 5
1. A1 — User Credentials
2. A2 — Customer Sensitive Data
3. A3 — Product & Inventory Data
4. A4 — Sales & Transaction Records
5. A5 — Encryption Keys & Security Configuration

#### Threats — exactly 5
1. T1 — SQL Injection
2. T2 — Cross-Site Scripting (XSS)
3. T3 — Unauthorized Access
4. T4 — CSRF / IDOR
5. T5 — Credential Attack (Brute Force)

#### Security Requirements — exactly 4

**SR1 — Secure Authentication**  
The system shall securely authenticate users using strong password hashing and shall provide
optional TOTP two-factor authentication; it shall block an account after three consecutive
failed login attempts and rate-limit login requests.

**SR2 — Access Control**  
The system shall enforce RBAC to ensure that each user can access only the resources and operations authorized for their role.

**SR3 — Data Protection**  
The system shall protect sensitive data using strong encryption and secure key management.

**SR4 — Secure Input and Requests**  
The system shall validate and sanitize user input and protect application requests against SQL Injection, XSS, CSRF, IDOR and Path Traversal attacks.

---

### 2. Abuse Cases — exactly 4

**AC1 — SQL Injection**  
A malicious user submits database control characters through a search or form input to attempt unauthorized database access or modification.

**AC2 — XSS Attack**  
A malicious user submits script content as a product/customer field and attempts to execute it in another user's browser.

**AC3 — Unauthorized Resource Access**  
A lower-privileged user attempts to access an administrative endpoint or a resource belonging to another user.

**AC4 — Brute Force Login**  
An attacker repeatedly submits incorrect passwords to compromise an account.

### Security Use Cases — exactly 4

**SUC1 — Secure Login**  
User → validate input → locate account → verify password hash → check lock state →
(if 2FA enabled) verify TOTP code → create secure session → audit event.

**SUC2 — Authorized CRUD**  
User → authenticate → RBAC check → validate/sanitize input → perform CRUD operation → audit event.

**SUC3 — Secure Sale Transaction**  
Employee/Manager → select customer/product → validate → check stock → create Sale → create SaleItem → decrease inventory → commit; on failure rollback.

**SUC4 — Secure Sensitive Data Access**  
Authorized user → authenticate → authorize → decrypt sensitive customer field → display only through authorized page.

---

## 3. Threat Modeling

### STRIDE

| Category | Example in SecureStock | Control |
|---|---|---|
| Spoofing | Password / TOTP attack | Hashing + lockout + limiter + TOTP 2FA |
| Tampering | Unauthorized inventory modification | RBAC + validation + transaction |
| Repudiation | Denying a sale | AuditLog |
| Information Disclosure | Exposing customer phone | Encryption + authorization |
| Denial of Service | Repeated login requests | Flask-Limiter |
| Elevation of Privilege | Employee accessing admin functions | RBAC decorators |

### DREAD

Score each category from 1–10. Risk = average of the five values.

| Threat | Damage | Reproducibility | Exploitability | Affected Users | Discoverability | Average |
|---|---:|---:|---:|---:|---:|---:|
| SQL Injection | 9 | 8 | 8 | 9 | 7 | 8.2 |
| XSS | 6 | 8 | 7 | 7 | 8 | 7.2 |
| Unauthorized Access | 9 | 7 | 7 | 9 | 6 | 7.6 |
| CSRF / IDOR | 8 | 7 | 7 | 8 | 7 | 7.4 |
| Credential Attack | 7 | 9 | 8 | 6 | 8 | 7.6 |

Risk treatment: SQL Injection, Unauthorized Access, IDOR/CSRF and Credential Attack receive high priority controls before deployment.

---

## 4. Secure Development Lifecycle

### Secure Design
- Least privilege.
- RBAC.
- Defense in depth.
- Secure defaults.
- Separation of Models, Routes and Templates.
- No secrets hardcoded in source.

### Secure Implementation
- SQLAlchemy ORM.
- Flask-WTF CSRF.
- Jinja autoescaping.
- Bleach sanitization.
- Werkzeug password hashing.
- Fernet encryption.
- Flask-Limiter.
- Secure filename handling.
- Explicit authorization checks.

### Secure Testing
Automatic test suite (74 tests) covering authentication, RBAC, CRUD, SQL Injection
resistance, XSS output encoding, CSRF rejection, IDOR authorization, Path Traversal
prevention, file-signature validation, rate limiting, lockout and transaction rollback,
plus static analysis (ruff) and an automated security scan (bandit — 0 issues).

### Secure Deployment
- Set a strong SECRET_KEY.
- Generate a strong FERNET_KEY.
- Use HTTPS.
- Set SESSION_COOKIE_SECURE=True.
- Disable debug mode.
- Use a production WSGI server.
- Restrict database and upload permissions.
- Keep dependencies updated.
- Back up the database securely.

### Maintenance
- Dependency updates.
- Periodic permission review.
- Log review.
- Security regression tests.
- Database backups.
- Key rotation procedure with controlled migration.

---

# Part Two: Implementation Mapping

| Requirement | Implementation |
|---|---|
| CRUD | Products, Customers, Users |
| Real-time DB | Flask-SQLAlchemy |
| Transactions | Sale + SaleItem + inventory update |
| RBAC | role_required decorator |
| XSS | Jinja autoescape + bleach |
| CSRF | Flask-WTF |
| IDOR | Sale ownership check for employees |
| SQL Injection | SQLAlchemy ORM / parameter binding |
| Path Traversal | secure_filename + resolved path validation |
| Input Validation | WTForms validators |
| Authentication | Flask-Login |
| Password hashing | Werkzeug scrypt |
| Cryptography | Fernet |
| Sessions | HttpOnly + SameSite + expiration |
| Error handling | Flask error handlers + rollback |
| Rate limiting | Flask-Limiter |
| 3-attempt lockout | User.failed_attempts + locked_until |
| Constant-time login anti-enumeration | DUMMY_HASH compare + generic message |
| TOTP 2FA | pyotp secret + verify + QR provisioning |
| Password change/reset | ChangePasswordForm + ResetPasswordForm, verified current password |
| Audit trail | AuditLog (admin viewer with pagination) |
| Pagination | per-page on every list page |
| CI | GitHub Actions (ruff + bandit + pytest) |
| Deployment | Waitress + Docker + Docker Compose |
| Separation | models/routes/templates |

---

# Part Three: Functional Requirements

FR1: Admin can create, read, and delete users.  
FR2: Admin/Manager can create, read, update and delete products.  
FR3: Authorized users can create and manage customers.  
FR4: Authorized users can adjust inventory.  
FR5: Authorized users can create sales.  
FR6: A sale decreases inventory and creates SaleItem records atomically.  
FR7: Employees can read only sales they created.  
FR8: The system records security-sensitive actions in AuditLog.  
FR9: Sensitive customer phone numbers are encrypted at rest.  
FR10: The system blocks an account after 3 failed attempts.  
FR11: Users can enable / disable TOTP two-factor authentication from their profile.  
FR12: The login flow requires a TOTP code for accounts with 2FA enabled.  
FR13: All list pages are paginated.  
FR14: Users can change their own password after verifying their current password.  
FR15: An admin can reset another user's password; the reset also clears any lockout.

---

# Demonstration Script for the Instructor

1. Login as Employee.
2. Show dashboard and role.
3. Create a customer.
4. Create a sale.
5. Show that inventory decreases.
6. Open the sale details.
7. Try `/users/` as Employee → 403.
8. Login as Admin → Users become accessible.
9. Submit `<script>alert(1)</script>` as a product name → it is rendered safely.
10. Try a SQL-like search string → no SQL is executed.
11. Submit a POST without CSRF token using a test client → request rejected.
12. Try to open another employee's sale → 403.
13. Try a filename such as `../../secret.txt` → sanitized/rejected.
14. Fail login 3 times → account is locked.
15. Show the database: passwords are hashes and customer phone is encrypted ciphertext.
16. Show AuditLog (with pagination).
17. Demonstrate a failed sale with insufficient stock → no partial database changes.
18. As a user, enable TOTP 2FA in Profile → scan the QR → confirm with the app code
    → log out → log in → the second-factor screen requires a TOTP code.
19. As Admin, open `/audit/` and show TFA_ENROLL_STARTED / TFA_ENABLED and LOGIN events.
20. As a user, change your password (requires the current password) → old password no
    longer works; the change appears in the audit trail.
21. As Admin, reset an employee's password from the Users page → the employee can log in
    with the new password, and PASSWORD_RESET is recorded.
