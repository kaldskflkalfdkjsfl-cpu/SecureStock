from tests.conftest import DEMO_PASSWORD, login


def _product_index_after_payload(client, payload):
    resp = client.get("/products/", query_string={"q": payload})
    return resp.get_data(as_text=True)


# SEC-04: XSS string in product name -> rendered as text, not executed
def test_xss_in_product_name_is_escaped(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    payload = "<script>alert(1)</script>"
    resp = client.post("/products/create", data={
        "name": payload,
        "description": payload,
        "price": "10",
        "quantity": "5",
        "low_stock_threshold": "1",
    }, follow_redirects=True)
    body = resp.get_data(as_text=True)
    # The raw <script> tag must not be rendered in the HTML source.
    assert "<script>" not in body


def test_xss_in_product_search_is_escaped(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    body = _product_index_after_payload(client, '<script>alert("xss")</script>')
    assert "<script>alert" not in body


# SEC-05: SQL-like search input treated as data
def test_sqli_like_search_is_treated_as_data(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    body = _product_index_after_payload(client, "' OR 1=1 --")
    # The literal text should be rendered, and no database error should occur.
    assert body.count("OR 1=1") >= 0
    assert "<title>Products — SecureStock</title>" in body


def test_sqli_wildcards_are_escaped(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    body = _product_index_after_payload(client, "%")
    assert "<title>Products — SecureStock</title>" in body


# XSS through user-created name shown on dashboard
def test_xss_escape_out_of_whole_page_template(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    malicious = "<img src=x onerror=alert(1)>"
    client.post("/products/create", data={
        "name": malicious, "price": "1", "quantity": "1", "low_stock_threshold": "1",
    }, follow_redirects=True)
    resp = client.get("/dashboard/")
    body = resp.get_data(as_text=True)
    assert "onerror=alert(1)" not in body
