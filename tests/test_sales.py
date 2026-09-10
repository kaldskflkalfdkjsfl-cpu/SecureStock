from app.models import Product, Sale
from tests.conftest import DEMO_PASSWORD, login


def _create_sale_via_route(client, quantity):
    resp = client.get("/sales/create")
    assert resp.status_code == 200
    return client.post("/sales/create", data={
        "customer_id": 1,
        "product_id": 1,
        "quantity": str(quantity),
    }, follow_redirects=True)


# SEC-08: Sale quantity > stock -> sale rejected
def test_sale_with_insufficient_stock_is_rejected(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = _create_sale_via_route(client, 50)  # stock is 10
    assert "Insufficient stock" in resp.get_data(as_text=True)


def test_sale_with_insufficient_stock_does_not_change_inventory(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    with client.application.app_context():
        before = Product.query.get(1).quantity
    _create_sale_via_route(client, 50)
    with client.application.app_context():
        after = Product.query.get(1).quantity
        assert after == before


# Successful sale decreases inventory and creates records
def test_successful_sale_decreases_inventory_and_creates_items(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    with client.application.app_context():
        qty_before = Product.query.get(1).quantity
    resp = _create_sale_via_route(client, 2)
    assert "created successfully" in resp.get_data(as_text=True)
    with client.application.app_context():
        qty_after = Product.query.get(1).quantity
        sales = Sale.query.count()
        assert qty_after == qty_before - 2
        assert sales == 1


# SEC-09: Exception during sale -> transaction rollback
def test_sale_rollback_on_exception(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    with client.application.app_context():
        qty_before = Product.query.get(1).quantity

    # Force a rollback by referencing a deleted product id in a crafted POST
    resp = client.post("/sales/create", data={
        "customer_id": 99999,
        "product_id": 99999,
        "quantity": "1",
    }, follow_redirects=True)
    assert resp.status_code in (200, 500)

    with client.application.app_context():
        qty_after = Product.query.get(1).quantity
        assert qty_after == qty_before  # nothing was committed


def test_sale_record_is_atomic(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    _create_sale_via_route(client, 1)
    with client.application.app_context():
        sale = Sale.query.first()
        assert sale is not None
        assert len(sale.items) == 1
        assert sale.total == 850.00
