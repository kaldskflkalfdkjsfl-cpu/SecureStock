from app.models import AuditLog, Customer, User
from app.security import decrypt_value, encrypt_value
from tests.conftest import DEMO_PASSWORD, login


# SEC-10: Customer phone in DB -> stored encrypted, not plaintext
def test_customer_phone_is_encrypted_at_rest(client, app):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.post("/customers/create", data={
        "name": "Alice Smith",
        "email": "alice@test.example.com",
        "phone": "+1234567890",
    }, follow_redirects=True)
    assert "Customer created" in resp.get_data(as_text=True)

    with app.app_context():
        cust = Customer.query.filter_by(email="alice@test.example.com").first()
        raw = cust.phone_encrypted
        assert raw is not None
        # Plaintext must not be stored; Fernet uses base64url (gAAAAA...).
        assert raw.startswith("gAAAA")
        assert b"+1234567890" not in raw.encode()
        # Round-trip decrypt works.
        assert decrypt_value(raw) == "+1234567890"


def test_encrypt_decrypt_roundtrip():
    val = "+972501234567"
    assert decrypt_value(encrypt_value(val)) == val


def test_invalid_ciphertext_returns_unavailable():
    assert decrypt_value("garbage") == "[unavailable]"


# SEC-11: Password in DB -> strong hash, never plaintext
def test_password_stored_as_hash_never_plaintext(app):
    with app.app_context():
        user = User.query.filter_by(email="admin@test.example.com").first()
        assert user.password_hash.startswith("scrypt:")
        assert "ChangeMe123!" not in user.password_hash


# Audit logging of security-sensitive actions
def test_logout_is_audited(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.get("/login")  # get a csrf-free page; but logout is POST
    from app.models import AuditLog
    # logout route is POST (CSRF enabled forms provide token, but CSRF off here)
    resp = client.post("/logout", follow_redirects=True)
    assert resp.status_code == 200
    with client.application.app_context():
        assert AuditLog.query.filter_by(action="LOGOUT").count() == 1


def test_user_creation_is_audited(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    client.post("/users/create", data={
        "name": "New User",
        "email": "newuser@test.example.com",
        "role": "employee",
        "password": "Str0ngPass!",
    }, follow_redirects=True)
    with client.application.app_context():
        assert AuditLog.query.filter_by(action="USER_CREATED").count() == 1
