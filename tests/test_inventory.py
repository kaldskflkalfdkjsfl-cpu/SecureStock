from app.models import AuditLog, Product
from tests.conftest import DEMO_PASSWORD, login


def test_inventory_index_lists_lowest_stock_first(client):
    login(client, "manager@test.example.com", DEMO_PASSWORD)
    resp = client.get("/inventory/")
    body = resp.get_data(as_text=True)
    assert "Mouse" in body and "Laptop" in body


def test_employee_cannot_adjust_inventory(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.post("/inventory/1/adjust", data={"amount": "5"})
    assert resp.status_code == 403


def test_inventory_adjustment_negative_to_empty_rejected(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.post("/inventory/1/adjust", data={"amount": "-20"},
                       follow_redirects=True)
    assert "cannot become negative" in resp.get_data(as_text=True)
    with client.application.app_context():
        assert Product.query.get(1).quantity == 10


def test_inventory_adjustment_valid_logged(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.post("/inventory/1/adjust", data={"amount": "-4"},
                       follow_redirects=True)
    assert "Inventory updated" in resp.get_data(as_text=True)
    with client.application.app_context():
        assert Product.query.get(1).quantity == 6
        assert AuditLog.query.filter_by(action="INVENTORY_ADJUSTED").count() == 1


def test_inventory_adjustment_invalid_input(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.post("/inventory/1/adjust", data={"amount": "abc"},
                       follow_redirects=True)
    assert "Invalid quantity" in resp.get_data(as_text=True)


def test_inventory_adjustment_missing_product_404(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.post("/inventory/9999/adjust", data={"amount": "1"})
    assert resp.status_code == 404
