import os
import tempfile

from app import create_app
from app.extensions import db
from app.models import User
from app.security import hash_password
from tests.conftest import DEMO_PASSWORD


def _csrf_enabled_app():
    fd, path = tempfile.mkstemp()
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{path}",
        WTF_CSRF_ENABLED=True,
        RATELIMIT_ENABLED=False,
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(User(email="admin@test.example.com", name="Admin", role="admin",
                            password_hash=hash_password(DEMO_PASSWORD)))
        db.session.commit()
    return app, fd, path


# SEC-06: POST without CSRF token -> rejected
def test_post_without_csrf_token_is_rejected():
    app, fd, path = _csrf_enabled_app()
    client = app.test_client()

    # Login first (send CSRF token with login requests)
    resp = client.get("/login")
    import re
    token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"',
                      resp.get_data(as_text=True)).group(1)
    client.post("/login", data={"email": "admin@test.example.com", "password": DEMO_PASSWORD,
                                "csrf_token": token}, follow_redirects=True)

    # POST a product create WITHOUT the CSRF token
    resp = client.post("/products/create", data={
        "name": "No CSRF",
        "price": "10",
        "quantity": "5",
        "low_stock_threshold": "1",
    })
    assert resp.status_code == 400

    os.close(fd)
    os.unlink(path)


def test_post_with_valid_csrf_token_is_accepted():
    app, fd, path = _csrf_enabled_app()
    client = app.test_client()

    resp = client.get("/login")
    import re
    token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"',
                      resp.get_data(as_text=True)).group(1)
    client.post("/login", data={"email": "admin@test.example.com", "password": DEMO_PASSWORD,
                                "csrf_token": token}, follow_redirects=True)

    # The session changes after login, so a fresh CSRF token must be obtained.
    resp = client.get("/products/create")
    token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"',
                      resp.get_data(as_text=True)).group(1)
    resp = client.post("/products/create", data={
        "name": "With CSRF",
        "price": "10",
        "quantity": "5",
        "low_stock_threshold": "1",
        "csrf_token": token,
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert "With CSRF" in resp.get_data(as_text=True)

    os.close(fd)
    os.unlink(path)
