# SecureStock — Secure Inventory & Sales Management System

A complete Flask practical project that demonstrates secure programming end-to-end:
security requirements engineering (5 assets, 5 threats, 4 requirements), threat modeling
(STRIDE & DREAD), abuse/security use cases, real CRUD, real sales transactions with
rollback, RBAC, and a hardened production deployment pipeline.

## Feature highlights

- **Authentication & access control** — RBAC (Admin / Manager / Employee) with Flask-Login,
  scrypt password hashing, account lockout after 3 failed logins, brute-force rate limiting,
  anti-enumeration constant-time login, session hardening.
- **TOTP two-factor authentication (2FA)** — enroll via QR code, verify on login, disable
  with code confirmation, and audit every step.
- **Sales engine** — transactional sale creation with stock validation and rollback on any
  exception; sales are atomic.
- **IDOR protection** — employees only see their own sales; managers/admins see all.
- **Data protection** — customer phone numbers encrypted at rest (Fernet), passwords hashed
  (scrypt), TLS-ready cookie flags.
- **Input hardening** — Jinja autoescaping + sanitized output, SQLAlchemy parameterized
  queries, Flask-WTF CSRF protection, file-upload validation (extension + magic-number
  signature + safe path), input validation.
- **Audit trail** — every security-relevant event (logins, lockouts, TFA enrollment,
  inventory adjustments, user/sale operations) is persisted and viewable by admins.
- **Observability & ops** — pagination everywhere, styled error pages, waitress production
  server, Docker images, GitHub Actions CI, Flask-Migrate schema versioning.
- **Credential lifecycle** — users change their own password (current password required);
  admins reset any user's password, which also clears an account lockout.

## 1. Installation

Python 3.11+ recommended (tested on 3.13).

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and change every value.

Generate a Fernet encryption key (used for `FERNET_KEY`):
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 2. Initialize the database

```bash
python seed.py
```

The seed script creates demo users, sample products, customers and a low-stock warning.

Demo accounts (change the passwords before any real deployment):

| Role     | Email                                   | Password      |
|----------|-----------------------------------------|---------------|
| Admin    | admin@securestock.example.com           | ChangeMe123!  |
| Manager  | manager@securestock.example.com         | ChangeMe123!  |
| Employee | employee@securestock.example.com        | ChangeMe123!  |

**Note:** the `.local` TLD is reserved (RFC 6762) and fails email validation, so the seed
uses `.example.com`.

## 3. Run

Development server:
```bash
python run.py
```

Production server (Waitress) — recommended for demos:
```bash
python serve.py
```

Open: http://127.0.0.1:5000

## 4. Run with Docker

```bash
docker compose up --build
```

Starts a containerized app on http://127.0.0.1:5000.

## 5. Database migrations

Schema changes are managed with Flask-Migrate:
```bash
flask db upgrade
```

## 6. Quality checks

```bash
# Lint (ruff: E, F, W, I, B, UP, S, SIM)
ruff check app tests

# Static security scan (bandit)
bandit -r app

# Full test suite (84 tests, ~91% coverage)
pytest --cov=app --cov-report=term-missing
```

Run locally for live testing during an audit:

```bash
bandit -r app -f html -o docs/reports/bandit.html
pytest --cov=app --cov-report=html:docs/reports/htmlcov --cov-report=xml:docs/reports/coverage.xml
```

## 7. Project structure

```text
SecureStock/
├── app/
│   ├── __init__.py          # app factory, error handlers, blueprint registration
│   ├── extensions.py        # db, login manager, CSRF, rate limiter
│   ├── models.py            # User, Product, Customer, Sale, SaleItem, AuditLog
│   ├── forms.py             # WTForms with strict validation
│   ├── security.py          # password/TOTP helpers, encryption, upload checks, RBAC
│   ├── security_headers.py  # CSP + HTTP headers
│   └── routes/
│       ├── auth.py          # login (rate-limited), 2FA verify, logout
│       ├── dashboard.py     # stats, low-stock, recent security activity
│       ├── users.py         # admin user management
│       ├── products.py      # CRUD + pagination + search
│       ├── customers.py     # CRUD + encrypted phone
│       ├── inventory.py     # stock adjustments (no negative stock)
│       ├── sales.py         # transactional sales, per-user scoping
│       ├── audit.py         # admin audit-trail viewer
│       └── profile.py       # TOTP 2FA enrollment/disable
├── migrations/              # Alembic/flask-migrate versions
├── tests/                   # 84 automated tests (auth, rbac, csrf, xss/sqli,
│                            # upload, sales, data protection, audit, inventory,
│                            # profile, crud)
├── docs/
│   ├── security_documentation.md
│   ├── ERD.md
│   ├── roles.md
│   └── TEST_PLAN.md
├── .github/workflows/ci.yml # lint + bandit + pytest on every push
├── Dockerfile
├── docker-compose.yml
├── requirements.txt         # production deps
├── requirements-dev.txt     # pytest, ruff, bandit, pytest-cov
├── pyproject.toml
├── config.py
├── run.py                   # dev server
├── serve.py                 # waitress production server
├── wsgi.py
├── seed.py
└── .env.example
```

## 8. Security design summary

Exact model used in the academic documentation:

### Assets — exactly 5
- A1 User Credentials
- A2 Customer Sensitive Data
- A3 Product & Inventory Data
- A4 Sales & Transaction Records
- A5 Encryption Keys & Security Configuration

### Threats — exactly 5
- T1 SQL Injection
- T2 XSS
- T3 Unauthorized Access
- T4 CSRF / IDOR
- T5 Credential Attack

### Security Requirements — exactly 4
- SR1 Secure Authentication
- SR2 Access Control
- SR3 Data Protection
- SR4 Secure Input and Requests

### Abuse Cases — exactly 4
- AC1 SQL Injection
- AC2 XSS Attack
- AC3 Unauthorized Resource Access
- AC4 Brute Force Login

### Security Use Cases — exactly 4
- SUC1 Secure Login
- SUC2 Authorized CRUD
- SUC3 Secure Sale Transaction
- SUC4 Secure Sensitive Data Access

Full documentation: `docs/security_documentation.md`.

## 9. Security test checklist

1. Wrong password 3× → account locked for 15 minutes (works across timezones).
2. Unknown email and known email return the same generic message; timing stays constant.
3. Employee hits `/users/` → 403.
4. Employee opens another employee's sale → 403.
5. `<script>alert(1)</script>` as product name → rendered as text, not executed.
6. Crafted SQL-like search string → ORM treats it as data (LIKE wildcards escaped).
7. POST without CSRF token → rejected.
8. `../../secret.txt` upload → path sanitized, magic-number check rejects mismatches.
9. Sale with insufficient stock → rejected, inventory unchanged (atomic, no partial writes).
10. Customer phone stored encrypted (Fernet) at rest; password stored as scrypt hash.
11. Inventory can never go negative at the application layer.
12. Every login/lockout/TFA/CRUD event appears in the admin audit trail.
13. Changing your password requires the current password; resets by an admin clear locks.

## 10. Important academic note

This project is intended for a controlled academic environment. It demonstrates defensive
secure-programming concepts. Run the abuse-case tests only against your own local
application.