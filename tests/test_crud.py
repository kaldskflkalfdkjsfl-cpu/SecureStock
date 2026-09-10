from app.models import AuditLog, Product, User
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
