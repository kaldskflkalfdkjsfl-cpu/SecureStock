import io

from tests.conftest import DEMO_PASSWORD, create_sale, login


# SEC-07: path traversal upload -> sanitized/rejected
def test_path_traversal_upload_is_rejected(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    with client.application.app_context():
        sale_id = create_sale(client.application, "admin@test.example.com")
    resp = client.post(f"/sales/{sale_id}/upload",
                       data={"file": (io.BytesIO(b"hello world"), "../../../../../secret.txt")},
                       content_type="multipart/form-data", follow_redirects=True)
    body = resp.get_data(as_text=True)
    # The traversal filename must not survive.
    assert "../../" not in body


def test_uploads_endpoint_rejects_traversal(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.get("/sales/uploads/../../etc/passwd")
    assert resp.status_code in (403, 404)


# Disallowed file extension -> rejected (content validation)
def test_upload_disallowed_extension_is_rejected(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    with client.application.app_context():
        sale_id = create_sale(client.application, "admin@test.example.com")
    resp = client.post(f"/sales/{sale_id}/upload",
                       data={"file": (io.BytesIO(b"<html></html>"), "evil.html")},
                       content_type="multipart/form-data", follow_redirects=True)
    assert "disallowed file" in resp.get_data(as_text=True) or \
           "Invalid, unsafe or disallowed file" in resp.get_data(as_text=True)


# Content signature mismatch: .png that is not a PNG -> rejected
def test_upload_png_with_wrong_content_is_rejected(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    with client.application.app_context():
        sale_id = create_sale(client.application, "admin@test.example.com")
    resp = client.post(f"/sales/{sale_id}/upload",
                       data={"file": (io.BytesIO(b"not a png"), "image.png")},
                       content_type="multipart/form-data", follow_redirects=True)
    assert "Invalid, unsafe or disallowed file" in resp.get_data(as_text=True)


def test_upload_valid_txt_is_accepted(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    with client.application.app_context():
        sale_id = create_sale(client.application, "admin@test.example.com")
    resp = client.post(f"/sales/{sale_id}/upload",
                       data={"file": (io.BytesIO(b"invoice note 123"), "invoice.txt")},
                       content_type="multipart/form-data", follow_redirects=True)
    assert "uploaded safely" in resp.get_data(as_text=True)
