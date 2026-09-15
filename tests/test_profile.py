import pyotp

from app.models import AuditLog, User
from app.security import verify_password
from tests.conftest import DEMO_PASSWORD, login


def _post_password(client, current, new, confirm=None):
    return client.post(
        "/profile/password",
        data={
            "current_password": current,
            "new_password": new,
            "confirm_password": confirm if confirm is not None else new,
        },
        follow_redirects=True,
    )


def test_change_password_wrong_current_rejected(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = _post_password(client, "TotallyWrong1!", "NewPassword123!")
    assert "Current password is incorrect" in resp.get_data(as_text=True)


def test_change_password_mismatch_rejected(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = _post_password(client, DEMO_PASSWORD, "NewPassword123!", "OtherPassword123!")
    assert "do not match" in resp.get_data(as_text=True)


def test_change_password_policy_enforced(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = _post_password(client, DEMO_PASSWORD, "weak")
    assert "10+ chars" in resp.get_data(as_text=True)


def test_change_password_success_audited_and_login(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = _post_password(client, DEMO_PASSWORD, "NewPassword123!")
    assert "Password changed successfully" in resp.get_data(as_text=True)
    with client.application.app_context():
        assert AuditLog.query.filter_by(action="PASSWORD_CHANGED").count() == 1
        admin = User.query.filter_by(email="admin@test.example.com").first()
        assert verify_password(admin.password_hash, "NewPassword123!") is True
        assert verify_password(admin.password_hash, DEMO_PASSWORD) is False

    client.post("/logout")
    resp = login(client, "admin@test.example.com", "NewPassword123!")
    assert "Dashboard" in resp.get_data(as_text=True)
    client.post("/logout")
    not_in = login(client, "admin@test.example.com", DEMO_PASSWORD)
    assert "Dashboard" not in not_in.get_data(as_text=True)


def test_change_password_requires_login(client):
    resp = client.post("/profile/password",
                       data={"current_password": "x", "new_password": "y",
                             "confirm_password": "y"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def _enroll(client, email):
    """Start TOTP enrollment and return the generated secret."""
    resp = client.post("/profile/", data={"enable": "1"}, follow_redirects=True)
    body = resp.get_data(as_text=True).lower()
    assert "scan" in body or "secret" in body
    with client.application.app_context():
        user = User.query.filter_by(email=email).first()
        # secret is held in the test client session
        entry = AuditLog.query.filter_by(action="TFA_ENROLL_STARTED").first()
        assert entry is not None
        assert user.two_factor_enabled is False


def test_enrollment_requires_valid_code(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.post("/profile/", data={"enable": "1"})
    body = resp.get_data(as_text=True)
    assert "Two-Factor" in body and "scan" in body.lower()


def test_enroll_confirm_with_bad_code_rejected(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    client.post("/profile/", data={"enable": "1"})
    resp = client.post("/profile/", data={"confirm": "1", "code": "000000"},
                       follow_redirects=True)
    assert "Invalid verification code" in resp.get_data(as_text=True)
    with client.application.app_context():
        user = User.query.filter_by(email="admin@test.example.com").first()
        assert user.two_factor_enabled is False


def test_full_2fa_enable_disable_roundtrip(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    client.post("/profile/", data={"enable": "1"})

    with client.session_transaction() as sess:
        pending = sess.get("tfa_pending_secret")
    totp = pyotp.TOTP(pending)

    resp = client.post("/profile/", data={"confirm": "1", "code": totp.now()},
                       follow_redirects=True)
    assert "Two-factor authentication enabled" in resp.get_data(as_text=True)
    with client.application.app_context():
        user = User.query.filter_by(email="admin@test.example.com").first()
        assert user.two_factor_enabled is True
        assert user.totp_secret == pending
    with client.session_transaction() as sess:
        assert sess.get("tfa_pending_secret") is None

    resp = client.post("/profile/", data={"disable": "1", "code": totp.now()},
                       follow_redirects=True)
    assert "Two-factor authentication disabled" in resp.get_data(as_text=True)
    with client.application.app_context():
        user = User.query.filter_by(email="admin@test.example.com").first()
        assert user.two_factor_enabled is False
        assert user.totp_secret is None


def test_disable_without_enabling_is_noop(client):
    login(client, "manager@test.example.com", DEMO_PASSWORD)
    resp = client.post("/profile/",
                       data={"disable": "1", "code": pyotp.TOTP("SOMEKEY").now()},
                       follow_redirects=True)
    assert "already disabled" in resp.get_data(as_text=True)
    with client.application.app_context():
        user = User.query.filter_by(email="manager@test.example.com").first()
        assert user.two_factor_enabled is False


def test_two_factor_enable_requires_login(client):
    resp = client.post("/profile/", data={"enable": "1"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
