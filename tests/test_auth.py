from datetime import UTC, datetime, timedelta

from app.extensions import db
from app.models import User
from tests.conftest import DEMO_PASSWORD, login


# SEC-01: 3 invalid logins -> account locked
def test_three_invalid_logins_lock_account(client):
    for _ in range(3):
        login(client, "admin@test.example.com", "WrongPassword1!")

    with client.application.app_context():
        user = User.query.filter_by(email="admin@test.example.com").first()
        assert user.failed_attempts == 0
        assert user.locked_until is not None


def test_locked_account_cannot_login(client):
    from app.extensions import db
    from app.models import User

    with client.application.app_context():
        user = User.query.filter_by(email="admin@test.example.com").first()
        user.locked_until = datetime.now(UTC) + timedelta(minutes=15)
        db.session.commit()

    resp = login(client, "admin@test.example.com", DEMO_PASSWORD)
    assert "Invalid credentials or account temporarily locked." in resp.get_data(as_text=True)


def test_lockout_expiry_allows_login_again(client):
    from app.models import User
    with client.application.app_context():
        user = User.query.filter_by(email="admin@test.example.com").first()
        # 12 minutes into the past => lock already expired
        user.locked_until = datetime.now(UTC) - timedelta(minutes=12)
        db.session.commit()

    resp = login(client, "admin@test.example.com", DEMO_PASSWORD)
    assert "<h2 class=\"h4 mb-1\">Secure Login</h2>" not in resp.get_data(as_text=True)


def test_successful_login_lands_on_dashboard(client):
    resp = login(client, "admin@test.example.com")
    assert "Dashboard" in resp.get_data(as_text=True)


def test_login_with_unknown_email_uses_generic_message(client):
    # Generic error must not reveal whether an account exists.
    resp = login(client, "nobody@test.example.com", "WrongPassword1!")
    body = resp.get_data(as_text=True)
    assert "Invalid credentials." in body


def test_unknown_account_failure_is_audited(client):
    from app.models import AuditLog
    login(client, "no-such-user@test.example.com", "Whatever1!")
    with client.application.app_context():
        logs = AuditLog.query.filter_by(action="LOGIN_FAILED_UNKNOWN").all()
        assert len(logs) == 1


def test_successful_login_is_audited(client):
    from app.models import AuditLog
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    with client.application.app_context():
        logs = AuditLog.query.filter_by(action="LOGIN_SUCCESS").all()
        assert len(logs) == 1


# SEC-12: Excessive login requests -> rate limit response 429
def test_rate_limit_blocks_excessive_logins():
    import os
    import tempfile

    from app import create_app
    from app.extensions import db
    from app.models import User
    from app.security import hash_password

    fd, path = tempfile.mkstemp()
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{path}",
        WTF_CSRF_ENABLED=False,
        RATELIMIT_ENABLED=True,
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(User(email="rl@test.example.com", name="RL", role="employee",
                            password_hash=hash_password(DEMO_PASSWORD)))
        db.session.commit()

    client = app.test_client()
    # The login endpoint allows 10 requests per minute.
    for _ in range(10):
        client.post(
            "/login",
            data={"email": "rl@test.example.com", "password": "bad"},
            follow_redirects=True,
        )
    resp = client.post("/login", data={"email": "rl@test.example.com", "password": "bad"},
                       follow_redirects=True)
    assert resp.status_code == 429
    os.close(fd)
    os.unlink(path)


# SEC-12 (TOTP): Two-step login
def test_totp_enabled_user_must_pass_second_factor(client):
    import pyotp

    from app.models import User

    with client.application.app_context():
        user = User.query.filter_by(email="admin@test.example.com").first()
        secret = pyotp.random_base32()
        user.totp_secret = secret
        db.session.commit()

    resp = login(client, "admin@test.example.com", DEMO_PASSWORD)
    body = resp.get_data(as_text=True)
    assert "Two-Factor Verification" in body

    # Wrong code rejected
    resp = client.post("/login/2fa", data={"code": "000000"}, follow_redirects=True)
    assert "Invalid verification code." in resp.get_data(as_text=True)

    # Correct code logs in
    totp = pyotp.TOTP(secret)
    resp = client.post("/login/2fa", data={"code": totp.now()}, follow_redirects=True)
    assert "Dashboard" in resp.get_data(as_text=True)


def test_totp_store_then_verify():
    import pyotp

    from app.security import generate_totp_secret, verify_totp_code
    secret = generate_totp_secret()
    assert len(secret) > 10
    totp = pyotp.TOTP(secret)
    assert verify_totp_code(secret, totp.now()) is True
    assert verify_totp_code(secret, "000000") is False
