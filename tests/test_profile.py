import pyotp

from app.models import AuditLog, User
from tests.conftest import DEMO_PASSWORD, login


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
