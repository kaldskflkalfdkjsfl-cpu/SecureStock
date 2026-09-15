import os
import tempfile

import pytest

os.environ["SECRET_KEY"] = "test-secret-key-long-enough"
os.environ["FERNET_KEY"] = "G2JqrCrOuuATxQgASq3rjN2wAzhW6NRkj6xkuv8pIpI="

from datetime import UTC

from app import create_app
from app.extensions import db
from app.models import Customer, Product, User
from app.security import hash_password


@pytest.fixture()
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(User(
            email="admin@test.example.com",
            name="Admin",
            role="admin",
            password_hash=hash_password("TestPassword123!")
        ))
        db.session.add(Product(name="Test", description="", price=10,
                               quantity=10, low_stock_threshold=2))
        db.session.add(Customer(name="Test Customer", email="customer@test.example.com"))
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture()
def client(app):
    return app.test_client()

def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Secure Login" in response.data

def test_user_is_locked_timezone_handling(app):
    from datetime import datetime, timedelta
    with app.app_context():
        user = User(
            email="locked@test.example.com",
            name="Locked User",
            role="employee",
            password_hash=hash_password("TestPassword123!"),
            locked_until=datetime.now(UTC) + timedelta(minutes=15)
        )
        db.session.add(user)
        db.session.commit()

        # Reload user from DB to simulate sqlite naive datetime retrieval
        reloaded = db.session.get(User, user.id)
        assert reloaded.is_locked() is True

def test_customer_phone_encryption(app):
    from app.security import encrypt_value
    with app.app_context():
        customer = Customer(
            name="Encrypted Cust",
            email="enc@test.example.com",
            phone_encrypted=encrypt_value("+123456789")
        )
        db.session.add(customer)
        db.session.commit()

        reloaded = db.session.get(Customer, customer.id)
        assert reloaded.phone == "+123456789"

def test_safe_upload_path_security(app):
    from app.security import safe_upload_path
    with app.app_context():
        path = safe_upload_path("document.pdf")
        assert path.name == "document.pdf"

        with pytest.raises(ValueError):
            safe_upload_path("../../")


def test_fixture_app_uses_temporary_database(app):
    """Guard: test apps must never bind to the production instance DB."""
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    assert uri.startswith("sqlite:///")
    assert "SecureStock/instance/securestock.db" not in uri
    assert "instance" not in uri.lower()

