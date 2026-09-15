import os
import tempfile

os.environ["SECRET_KEY"] = "test-secret-key-long-enough-for-tests"
os.environ["FERNET_KEY"] = "G2JqrCrOuuATxQgASq3rjN2wAzhW6NRkj6xkuv8pIpI="
os.environ["SESSION_COOKIE_SECURE"] = "False"

import pytest

from app import create_app
from app.extensions import db
from app.models import Customer, Product, User
from app.security import hash_password

DEMO_PASSWORD = "ChangeMe123!"


def _make_in_memory_app():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
    })
    return app, db_fd, db_path


@pytest.fixture()
def app():
    app, db_fd, db_path = _make_in_memory_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add_all([
            User(email="admin@test.example.com", name="Admin", role="admin",
                 password_hash=hash_password(DEMO_PASSWORD)),
            User(email="manager@test.example.com", name="Manager", role="manager",
                 password_hash=hash_password(DEMO_PASSWORD)),
            User(email="employee@test.example.com", name="Employee", role="employee",
                 password_hash=hash_password(DEMO_PASSWORD)),
            User(email="employee2@test.example.com", name="Employee Two", role="employee",
                 password_hash=hash_password(DEMO_PASSWORD)),
            Product(name="Laptop", description="", price=850.00,
                    quantity=10, low_stock_threshold=2),
            Product(name="Mouse", description="", price=25.00,
                    quantity=30, low_stock_threshold=5),
            Customer(name="Test Customer", email="customer@test.example.com"),
        ])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
    # Dispose the engine before closing the file on Windows.
    with app.app_context():
        db.engine.dispose()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email, password=DEMO_PASSWORD):
    """Perform a login request and return the response (follow_redirects=True)."""
    return client.post("/login", data={"email": email, "password": password},
                       follow_redirects=True)


def create_sale(app, by_email, customer_id=1, product_id=1, quantity=2):
    """Create a Sale for a given user (by email) via the ORM. Returns the sale id (int)."""
    from app.models import Sale, SaleItem
    user = User.query.filter_by(email=by_email).first()
    product = Product.query.get(product_id)
    customer = Customer.query.get(customer_id)
    sale = Sale(customer_id=customer.id, user_id=user.id,
                total=product.price * quantity)
    db.session.add(sale)
    db.session.flush()
    db.session.add(SaleItem(sale_id=sale.id, product_id=product.id,
                            quantity=quantity, unit_price=product.price))
    db.session.commit()
    return sale.id
