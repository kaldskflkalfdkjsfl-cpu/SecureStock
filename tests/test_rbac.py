from tests.conftest import DEMO_PASSWORD, create_sale, login


# SEC-02: Employee visits /users/ -> 403
def test_employee_cannot_access_users_page(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.get("/users/")
    assert resp.status_code == 403


def test_employee_cannot_create_users(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.post("/users/create", data={}, follow_redirects=True)
    assert resp.status_code == 403


def test_manager_cannot_access_users_page(client):
    login(client, "manager@test.example.com", DEMO_PASSWORD)
    resp = client.get("/users/")
    assert resp.status_code == 403


def test_admin_can_access_users_page(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.get("/users/")
    assert resp.status_code == 200


# SEC-03: Employee opens another employee's sale -> 403
def test_employee_cannot_open_other_employee_sale(client):
    with client.application.app_context():
        sale_id = create_sale(client.application, "employee2@test.example.com")
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.get(f"/sales/{sale_id}")
    assert resp.status_code == 403


def test_employee_can_open_own_sale(client):
    with client.application.app_context():
        sale_id = create_sale(client.application, "employee@test.example.com")
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.get(f"/sales/{sale_id}")
    assert resp.status_code == 200


def test_manager_can_open_any_sale(client):
    with client.application.app_context():
        sale_id = create_sale(client.application, "employee2@test.example.com")
    login(client, "manager@test.example.com", DEMO_PASSWORD)
    resp = client.get(f"/sales/{sale_id}")
    assert resp.status_code == 200


# IDOR: sales list must be scoped to the employee
def test_employee_sales_list_only_shows_own_sales(client):
    with client.application.app_context():
        mine_id = create_sale(client.application, "employee@test.example.com")
        create_sale(client.application, "employee2@test.example.com")
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.get("/sales/")
    body = resp.get_data(as_text=True)
    assert f"#{mine_id}" in body
    # Only one sale (the employee's own) should be visible.
    assert body.count("Test Customer") == 1


def test_manager_sales_list_shows_all_sales(client):
    with client.application.app_context():
        create_sale(client.application, "employee@test.example.com")
        create_sale(client.application, "employee2@test.example.com")
    login(client, "manager@test.example.com", DEMO_PASSWORD)
    resp = client.get("/sales/")
    body = resp.get_data(as_text=True)
    assert body.count("Test Customer") == 2


# RBAC matrix on CRUD pages
def test_employee_click_on_products_shows_read_only(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.get("/products/")
    assert "Read only" in resp.get_data(as_text=True)


def test_employee_cannot_be_allowed_to_create_products(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.get("/products/create")
    assert resp.status_code == 403


def test_employee_receives_403_on_products_create_post(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.post("/products/create", data={})
    assert resp.status_code == 403
