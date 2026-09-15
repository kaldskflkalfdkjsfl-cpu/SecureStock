from app.models import AuditLog, Product, User
from app.security import verify_password
from tests.conftest import DEMO_PASSWORD, login


def test_admin_can_edit_product(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.post("/products/1/edit", data={
        "name": "Laptop Pro",
        "description": "Updated",
        "price": "999.00",
        "quantity": "8",
        "low_stock_threshold": "3",
    }, follow_redirects=True)
    assert "Product updated" in resp.get_data(as_text=True)
    with client.application.app_context():
        assert Product.query.get(1).name == "Laptop Pro"
        assert AuditLog.query.filter_by(action="PRODUCT_UPDATED").count() == 1


def test_admin_can_delete_product(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.post("/products/2/delete", follow_redirects=True)
    assert "Product deleted" in resp.get_data(as_text=True)
    with client.application.app_context():
        assert Product.query.get(2) is None


def test_manager_can_delete_customer_without_sales(client):
    login(client, "manager@test.example.com", DEMO_PASSWORD)
    resp = client.post("/customers/1/delete", follow_redirects=True)
    assert "Customer deleted" in resp.get_data(as_text=True)


def test_employee_cannot_delete_customer(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.post("/customers/1/delete")
    assert resp.status_code == 403


def test_employee_cannot_edit_product(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.post("/products/1/edit", data={})
    assert resp.status_code == 403


def test_admin_cannot_delete_self(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    with client.application.app_context():
        admin_id = User.query.filter_by(email="admin@test.example.com").first().id
    resp = client.post(f"/users/{admin_id}/delete", follow_redirects=True)
    assert "You cannot delete yourself" in resp.get_data(as_text=True)


def test_employee_cannot_delete_user(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.post("/users/1/delete")
    assert resp.status_code == 403


def test_missing_resource_returns_styled_404(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.get("/products/999999/edit")
    assert resp.status_code == 404
    assert "Not Found" in resp.get_data(as_text=True)


def test_admin_sets_new_password(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.post("/users/2/reset-password",
                       data={"new_password": "ResetPass123!",
                             "confirm_password": "ResetPass123!"},
                       follow_redirects=True)
    assert "Password reset for manager@test.example.com" in resp.get_data(as_text=True)
    with client.application.app_context():
        manager = User.query.get(2)
        assert AuditLog.query.filter_by(action="PASSWORD_RESET").count() == 1
        assert verify_password(manager.password_hash, "ResetPass123!") is True

    client.post("/logout")
    resp = login(client, "manager@test.example.com", "ResetPass123!")
    assert "Dashboard" in resp.get_data(as_text=True)


def test_admin_reset_rejects_weak_and_mismatch(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.post("/users/2/reset-password",
                       data={"new_password": "weak", "confirm_password": "weak"},
                       follow_redirects=True)
    assert "10+ chars" in resp.get_data(as_text=True)
    resp = client.post("/users/2/reset-password",
                       data={"new_password": "GoodPass1!",
                             "confirm_password": "BadPass2@"},
                       follow_redirects=True)
    assert "do not match" in resp.get_data(as_text=True)


def test_admin_reset_missing_user_404(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.get("/users/9999/reset-password")
    assert resp.status_code == 404


def test_non_admin_cannot_reset_password(client):
    login(client, "manager@test.example.com", DEMO_PASSWORD)
    assert client.get("/users/1/reset-password").status_code == 403
    resp = client.post("/users/1/reset-password",
                       data={"new_password": "ResetPass123!",
                             "confirm_password": "ResetPass123!"})
    assert resp.status_code == 403
