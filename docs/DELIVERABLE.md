# SecureStock
### Secure Inventory & Sales Management System — Deliverable & Discussion Document
### نظام إدارة المخزون والمبيعات الآمن — وثيقة التسليم والمناقشة

| Field | Value |
|---|---|
| Project | SecureStock — Flask secure programming practical |
| Student | [Your Name] — [Student ID] |
| Course | Security Programming Practical Project |
| Language | Python 3.11+ · Flask 3.1 · SQLAlchemy 2 |
| Repository | https://github.com/kaldskflkalfdkjsfl-cpu/SecureStock |
| Verification | 94 automated tests · ~91% coverage · bandit 0 issues |

---

## 1. Overview / نظرة عامة

SecureStock is a complete **inventory and sales management system** built with Flask,
designed from the ground up as a *secure programming* exercise. Every layer follows
defense-in-depth: strong authentication, role-based access control, encrypted sensitive
data, sanitized input/output, transactional business logic, and a full audit trail.

سيكنستوك نظام متكامل لإدارة المخزون والمبيعات مبني بإطار Flask، صُمِّم كتمرين برمجي آمن:
مصادقة قوية، تحكم وصول بالصلاحيات، تشفير البيانات الحساسة، تعقيم الإدخال والإخراج، منطق
معاملات متكامل، وسجل تدقيق شامل.

### 1.1 Functional Scope
- User management (admin) with pagination
- Product & customer CRUD
- Inventory adjustments (quantity never negative)
- Transactional sales (stock check + Sale/SaleItem + rollback)
- Two-factor authentication (TOTP) and password lifecycle
- Audit-trail viewer (admin)

### 1.2 Tech Stack
| Layer | Technology |
|---|---|
| Language | Python 3.11–3.13 |
| Web framework | Flask 3.1 |
| ORM | Flask-SQLAlchemy 2 (parameterized queries) |
| Forms/CSRF | Flask-WTF |
| Auth | Flask-Login + Werkzeug scrypt |
| Encryption | cryptography (Fernet) |
| 2FA | pyotp (RFC 6238 TOTP) |
| Sanitization | bleach |
| Rate limiting | Flask-Limiter |
| Migrations | Flask-Migrate |
| Server | Waitress (production), Flask dev server |
| Ops | Docker + docker-compose + GitHub Actions CI |
| Quality | pytest + pytest-cov + ruff + bandit |

---

## 2. Security Requirements Engineering / هندسة المتطلبات الأمنية

### 2.1 Assets — exactly 5 / الأصول — 5 بالضبط
| ID | Asset | Asset (AR) |
|---|---|---|
| A1 | User Credentials | بيانات اعتماد المستخدمين |
| A2 | Customer Sensitive Data | البيانات الحساسة للعملاء |
| A3 | Product & Inventory Data | بيانات المنتجات والمخزون |
| A4 | Sales & Transaction Records | سجلات المبيعات والمعاملات |
| A5 | Encryption Keys & Security Configuration | مفاتيح التشفير والإعدادات الأمنية |

### 2.2 Threats — exactly 5 / التهديدات — 5 بالضبط
| ID | Threat | Threat (AR) |
|---|---|---|
| T1 | SQL Injection | حقن SQL |
| T2 | Cross-Site Scripting (XSS) | البرمجة النصية عبر المواقع |
| T3 | Unauthorized Access | وصول غير مصرّح به |
| T4 | CSRF / IDOR | تزوير الطلبات / الوصول المباشر غير المصرح |
| T5 | Credential Attack (Brute Force) | هجوم البيانات الاعتمادية |

### 2.3 Security Requirements — exactly 4 / المتطلبات الأمنية — 4 بالضبط
**SR1 — Secure Authentication / مصادقة آمنة**  
Strong scrypt password hashing, optional TOTP two-factor authentication, account lockout
after 3 failed attempts, login rate-limiting, constant-time authentication against account
existence.

**SR2 — Access Control / التحكم في الوصول**  
RBAC (Admin/Manager/Employee) enforced server-side on every endpoint via `role_required()`;

**SR3 — Data Protection / حماية البيانات**  
Customer phone stored Fernet-encrypted; passwords stored as scrypt hashes; secure session
cookie flags; encryption keys only in environment.

**SR4 — Secure Input and Requests / إدخال وطلبات آمنة**  
Input validation on all forms, sanitization with bleach, CSRF tokens, parameterized queries,
upload signature checks, security headers + CSP.

---

## 3. Abuse Cases & Security Use Cases / حالات الإساءة وحالات الاستخدام الأمني

### 3.1 Abuse Cases — exactly 4 / حالات الإساءة — 4 بالضبط
| ID | Case | Defense |
|---|---|---|
| AC1 | SQL Injection via search/forms | SQLAlchemy parameterized queries + LIKE-escape |
| AC2 | XSS script injection in name/description | Jinja autoescape + bleach sanitize |
| AC3 | Unauthorized resource access (IDOR/privilege) | `role_required` + ownership checks |
| AC4 | Brute-force login | Lockout + rate limit + constant-time compare |

### 3.2 Security Use Cases — exactly 4 / حالات الاستخدام الأمني — 4 بالضبط
**SUC1 — Secure Login**  
validate input → locate user → **verify scrypt hash (constant-time, dummy-hash for unknown)** →
check lock state → (TOTP if enabled) → create session → audit event.

**SUC2 — Authorized CRUD**  
authenticate → authorize (RBAC) → validate/sanitize → perform CRUD → audit event.

**SUC3 — Secure Sale Transaction**  
validate → check stock → create Sale → create SaleItem → decrement stock → commit;
any exception → full rollback (atomicity tested).

**SUC4 — Secure Sensitive Data Access**  
authenticate → authorize → decrypt customer phone (Fernet) → display via authorized pages only.

---

## 4. Threat Modeling / نمذجة التهديدات

### 4.1 STRIDE
| Category | Example | Control | Control (AR) |
|---|---|---|---|
| Spoofing | password / TOTP attack | scrypt + lockout + limiter + TOTP | تجنب انتحال الهوية |
| Tampering | unauthorized inventory change | RBAC + validation + transactions | منع العبث |
| Repudiation | denying a sale | AuditLog trail | منع التنصّل |
| Information Disclosure | exposing customer phone | Fernet encryption + authorization | منع تسريب البيانات |
| Denial of Service | repeated logins | Flask-Limiter | منع الحرمان من الخدمة |
| Elevation of Privilege | employee hitting admin routes | role checks on every endpoint | منع تصعيد الصلاحية |

### 4.2 DREAD (1–10, Risk = average)
| Threat | D | R | E | A | D | Average |
|---|---:|---:|---:|---:|---:|---:|
| SQL Injection | 9 | 8 | 8 | 9 | 7 | **8.2** |
| XSS | 6 | 8 | 7 | 7 | 8 | **7.2** |
| Unauthorized Access | 9 | 7 | 7 | 9 | 6 | **7.6** |
| CSRF / IDOR | 8 | 7 | 7 | 8 | 7 | **7.4** |
| Credential Attack | 7 | 9 | 8 | 6 | 8 | **7.6** |

Top risks (SQL Injection, Unauthorized Access, Credential Attack) receive priority controls.

---

## 5. Security Algorithms in Practice / الخوارزميات الأمنية تطبيقياً

### 5.1 Password Hashing — scrypt (`app/security.py`)
```python
generate_password_hash(password, method="scrypt")
# scrypt:32768:8:1$salt$hash
```
- Memory-hard KDF (RFC 7914): resists GPU/ASIC parallelism.
- Per-user random salt → resists rainbow tables.
- Verification uses `hmac.compare_digest` → **constant-time comparison**.

### 5.2 Session & CSRF Signing — HMAC-SHA256
- Flask signs the session cookie with `SECRET_KEY` (itsdangerous → HMAC-SHA256 + timestamp).
- CSRF: synchronizer-token pattern, signed and bound to the session, 1-hour expiry
  (`WTF_CSRF_TIME_LIMIT = 3600`).

### 5.3 At-Rest Encryption — Fernet (`cryptography`)
`Fernet` = **AES-128-CBC + HMAC-SHA256 (encrypt-then-MAC)** + random IV + timestamp.
Applied to `Customer.phone_encrypted`; an invalid token returns `[unavailable]`.

### 5.4 TOTP 2FA — HMAC-SHA1 (RFC 6238)
`TOTP = Truncate(HMAC-SHA1(Base32Decode(secret), floor(time/30)))` — 6 digits, 30-second steps,
`valid_window=1` tolerance. QR provisioning URI `otpauth://totp/SecureStock:...`.

### 5.5 Anti-Enumeration / Timing
Login verifies against `DUMMY_HASH` when the account does not exist, so response timing does
not reveal account existence; identical generic error message in all failure paths.

### 5.6 Input & Output Hardening
- SQLi: parameterized ORM queries + LIKE wildcard escaping (`%`, `_`, `\`).
- XSS: Jinja2 autoescaping + `bleach.clean()` strip-all then length-limit (`sanitize_text`).
- Uploads: extension whitelist + **magic-byte signature** (`%PDF`, `\x89PNG...`, `\xff\xd8\xff`)
  + `secure_filename` + resolved-path containment + 2 MB limit.
- Regex validation: email, phone, 6-digit TOTP, strong-password policy.

### 5.7 Session Hardening & Headers
`HttpOnly` · `SameSite=Lax` · `Secure` (env) · 8-hour absolute cookie lifetime, plus
server-enforced **30-min idle** and **8-hour absolute** timeouts (`config.py:22-26`,
checked per request in `user_loader`). Beyond the signed cookie, every session carries a
server-side **revocable stamp** (`User.session_token`, `app/models.py:18`): rotating it
instantly invalidates all other sessions on password change (`profile.py:125`), admin
reset (`users.py:108`) and the "sign out all devices" action (`profile.py:138-148`).
Also `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, and a
strict Content-Security-Policy. Verified by `tests/test_session_security.py`.

---

## 6. Implementation Mapping / خريطة التنفيذ

| Requirement | Implementation |
|---|---|
| CRUD | Users, Products, Customers + pagination |
| Real DB | Flask-SQLAlchemy |
| Transactions | Sale + SaleItem + stock decrement, rollback tests |
| RBAC | `role_required("admin", ...)` decorator |
| XSS | Jinja autoescape + bleach |
| CSRF | Flask-WTF |
| IDOR | ownership checks (employees see own sales) |
| SQLi | parameterized ORM queries |
| Path traversal | `secure_filename` + resolved path + signature check |
| Auth | Flask-Login + scrypt + TOTP |
| Crypto | Fernet |
| Sessions | HttpOnly / SameSite / lifetime / server-side stamp + idle-absolute timeout |
| Errors | styled 400/403/404/429/500 handlers |
| Rate limiting | Flask-Limiter |
| Lockout | `failed_attempts` + `locked_until` (UTC-normalized) |
| Audit trail | AuditLog + admin viewer |
| Password lifecycle | self change + admin reset (clears lockout) |
| Separation | models / routes / templates |

---

## 7. RBAC Matrix

| Operation | Admin | Manager | Employee |
|---|---:|---:|---:|
| Dashboard | Yes | Yes | Yes |
| Manage users / reset passwords | Yes | No | No |
| Products CRUD | Yes | Yes | Read-only |
| Customers create | Yes | Yes | Yes |
| Customers update/delete | Yes | Yes | No |
| Inventory adjust | Yes | Yes | No |
| Create sales | Yes | Yes | Yes |
| Read own sales | Yes | Yes | Yes |
| Read all sales | Yes | Yes | No |
| View audit log | Yes | No | No |
| Profile / password / 2FA | Yes | Yes | Yes |

---

## 8. Data Model (ERD)

```
USER ──1:N── SALE ──1:N── SALE_ITEM :N──1 PRODUCT
USER ──1:N── AUDIT_LOG (user_id nullable)
CUSTOMER ──1:N── SALE
```
- `User`: id, email(unique), name, password_hash, role, failed_attempts, locked_until, totp_secret
- `Product`: id, name, description, price, quantity, low_stock_threshold
- `Customer`: id, name, email, phone_encrypted
- `Sale`: id, customer_id, user_id, total
- `SaleItem`: id, sale_id, product_id, quantity, unit_price
- `AuditLog`: id, user_id, action, entity, entity_id, ip_address, created_at

All timestamps stored as UTC; `is_locked()` normalizes naive datetimes for portability.

---

## 9. Verification & Testing / التحقق والاختبار

Run:
```bash
pip install -r requirements-dev.txt
ruff check app tests                       # static lint
bandit -r app                              # security scan
pytest --cov=app --cov-report=term-missing # 94 tests, ~91% coverage
```

### Results
| Check | Result |
|---|---|
| pytest | **94 passed** |
| Coverage | **~91%** (app/) |
| bandit (app) | **0 issues** |
| ruff | **All checks passed** |
| CI (GitHub Actions) | Python 3.11 & 3.12: lint + tests + bandit + secrets scan |

### Coverage by test area (13 files)
`test_auth` · `test_rbac` · `test_csrf` · `test_xss_sqli` · `test_upload` · `test_sales` ·
`test_data_protection` · `test_audit` · `test_inventory` · `test_profile` · `test_crud` ·
`test_security` · `test_session_security`

### Security checklist (all automated)
1. 3 wrong passwords → lockout (timezone-safe) · 2. unknown email → same error/timing ·
3. employee → `/users/` = 403 · 4. employee opens other's sale = 403 (IDOR) ·
5. `<script>` rendered as text · 6. SQL-like search treated as data · 7. POST without CSRF = 400 ·
8. `../../secret.txt` upload rejected · 9. PNG renamed to `.txt` rejected (signature) ·
10. insufficient-stock sale rejected atomically · 11. negative inventory rejected ·
12. phone encrypted at rest · 13. password never plaintext · 14. login rate limit = 429 ·
15. TOTP enforcement loop · 16. admin cannot delete self · 17. audit rows for every event.

> **Note:** Test isolation is enforced — a guard test verifies fixtures never bind to the
> production `instance/securestock.db`.

---

## 10. Deployment / النشر

- **Production**: `python seed.py && python serve.py` (Waitress) → http://127.0.0.1:5000
- **Docker**: `docker compose up --build` (non-root user, volumes for DB & uploads, healthcheck)
- **Migrations**: `flask db upgrade`
- **CI**: GitHub Actions on every push/PR (`master`/`main`)
- **Environment**: `.env` holds `SECRET_KEY`, `FERNET_KEY`, `SESSION_COOKIE_SECURE`

### Demo accounts (change before real deployment)
| Role | Email | Password |
|---|---|---|
| Admin | admin@securestock.example.com | ChangeMe123! |
| Manager | manager@securestock.example.com | ChangeMe123! |
| Employee | employee@securestock.example.com | ChangeMe123! |

> Note: `.local` is a reserved TLD (RFC 6762) and fails email validation, so the seed uses
> `.example.com`.

---

## 11. Ready-To-Run Discussion Script / دليل العرض الجاهز

1. **Employee login** → dashboard → create customer → create sale → inventory decreases
   → open sale detail (own sales only).
2. **Denial demos**: `/users/` as employee → 403; another employee's sale → 403;
   `<script>` as product name → safe output; SQL-like search → no error, no injection.
3. **CSRF demo**: curl a POST without token → 400.
4. **Upload demo**: `../../secret.txt` and `fake.png` (renamed exe) → rejected by
   signature/sanitization.
5. **Lockout demo**: 3 wrong passwords → account locked 15 min; verify raid log entry.
6. **2FA demo**: enable TOTP in Profile → scan QR → confirm → logout → second factor at login.
7. **Password lifecycle**: change own password (old required); admin resets a user
   (also unlocks) — both events in the audit log.
8. **DB evidence**: passwords are scrypt hashes; customer phone is Fernet ciphertext.
9. **Audit trail demo** (admin): LOGIN_SUCCESS/FAILED, TFA_*, PASSWORD_*, INVENTORY_ADJUSTED,
   USER_CREATED, SALE_*, with pagination and filtering.
10. **Quality evidence**: `pytest` (94 passed, ~91%), `bandit` (0 issues), CI badges/output.

---

## 12. Likely Discussion Questions / أبرز أسئلة المناقشة

- **Why scrypt and not SHA-256?** Memory-hard KDF → resists GPU/ASIC parallel brute force;
  salted → resists rainbow tables.
- **Why Fernet for the phone?** Encrypt-then-MAC (AES-CBC + HMAC) → confidentiality +
  integrity; misuse-resistant by design.
- **Can CSRF be bypassed?** Tokens bound to the session, 1-h expiry, SameSite=Lax, and
  `SESSION_COOKIE_SECURE` in production — layered.
- **How do you prevent SQLi with LIKE?** ORM binds parameters; wildcards are explicitly
  escaped so `%`/`_` stay data.
- **What if a sale fails mid-writing?** `db.session.commit()` after full flow; on exception
  the session rolls back — verified by atomicity tests.
- **How does account lockout survive timezones?** All times stored UTC; retrieval normalizes
  naive datetimes to UTC before comparison.
- **Why is the login page slow even for unknown users?** Deliberate — a dummy scrypt compare
  equalizes timing (anti-enumeration).

---

## 13. References / المراجع
- RFC 7914 (scrypt), RFC 6238 (TOTP), RFC 6749, RFC 6762 (.local reserved)
- OWASP Top 10 & OWASP ASVS
- Flask, Flask-SQLAlchemy, Flask-WTF, Werkzeug, cryptography (Fernet) documentation
- pytest, ruff, bandit tool documentation

---
*Prepared for submission & defense. All verification results are reproducible with the
commands shown in Section 9.*