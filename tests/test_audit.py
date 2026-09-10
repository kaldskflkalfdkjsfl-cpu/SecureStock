from app.models import AuditLog
from tests.conftest import DEMO_PASSWORD, login


def test_employee_cannot_view_audit_log(client):
    login(client, "employee@test.example.com", DEMO_PASSWORD)
    resp = client.get("/audit/")
    assert resp.status_code == 403


def test_manager_cannot_view_audit_log(client):
    login(client, "manager@test.example.com", DEMO_PASSWORD)
    resp = client.get("/audit/")
    assert resp.status_code == 403


def test_audit_log_shows_login_events(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    login(client, "manager@test.example.com", DEMO_PASSWORD)
    resp = client.get("/audit/")
    body = resp.get_data(as_text=True)
    assert "LOGIN_SUCCESS" in body
    assert "admin@test.example.com" in body


def test_audit_log_filter_by_action(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.get("/audit/?action=LOGIN_SUCCESS")
    assert "LOGIN_SUCCESS" in resp.get_data(as_text=True)


def test_audit_log_records_failed_logins_after_dummy_compare(client):
    client.post("/login", data={"email": "admin@test.example.com", "password": "wrong"},
                follow_redirects=True)
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    resp = client.get("/audit/")
    assert "LOGIN_FAILED" in resp.get_data(as_text=True)


def test_login_events_stored_with_audit_rows(client):
    login(client, "admin@test.example.com", DEMO_PASSWORD)
    with client.application.app_context():
        assert AuditLog.query.filter_by(action="LOGIN_SUCCESS").count() >= 1
        assert AuditLog.query.filter_by(entity="User").count() >= 1
