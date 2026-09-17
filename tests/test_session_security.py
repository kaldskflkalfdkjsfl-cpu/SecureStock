from app.models import User
from app.security import SESSION_SEEN_KEY, SESSION_STAMP_KEY, SESSION_STARTED_KEY
from tests.conftest import DEMO_PASSWORD, login

ADMIN = "admin@test.example.com"
NEW_PASSWORD = "NewSecret456!"


def _dashboard_ok(client):
    body = client.get("/dashboard/", follow_redirects=True).get_data(as_text=True)
    return "Dashboard" in body


def _logged_out(client):
    return client.get("/dashboard/").status_code == 302


def test_login_binds_server_side_stamp(client):
    login(client, ADMIN)
    with client.session_transaction() as sess:
        stamp = sess.get(SESSION_STAMP_KEY)
    assert stamp
    with client.application.app_context():
        user = User.query.filter_by(email=ADMIN).first()
        assert user.session_token == stamp


def test_multiple_devices_share_the_stamp(app, client):
    login(client, ADMIN)
    other = app.test_client()
    login(other, ADMIN)
    # Both devices stay authenticated at the same time (multi-session).
    assert _dashboard_ok(client)
    assert _dashboard_ok(other)


def test_missing_stamp_is_rejected(client):
    login(client, ADMIN)
    with client.session_transaction() as sess:
        sess.pop(SESSION_STAMP_KEY, None)
    assert _logged_out(client)


def test_tampered_stamp_is_rejected(client):
    login(client, ADMIN)
    with client.session_transaction() as sess:
        sess[SESSION_STAMP_KEY] = "forged-value"
    assert _logged_out(client)


def test_missing_user_is_rejected(client):
    login(client, ADMIN)
    with client.session_transaction() as sess:
        sess["_user_id"] = "999999"
    assert _logged_out(client)


def test_password_change_revokes_other_sessions(app, client):
    login(client, ADMIN)            # device A
    other = app.test_client()
    login(other, ADMIN)             # device B (same stamp)
    assert _dashboard_ok(other)

    resp = other.post("/profile/password", data={
        "current_password": DEMO_PASSWORD,
        "new_password": NEW_PASSWORD,
        "confirm_password": NEW_PASSWORD,
    }, follow_redirects=True)
    assert "Password changed successfully." in resp.get_data(as_text=True)

    # The device that changed the password stays logged in...
    assert _dashboard_ok(other)
    # ...while every other session is invalidated immediately.
    assert _logged_out(client)


def test_admin_reset_revokes_target_sessions(app, client):
    login(client, "employee@test.example.com")     # victim device
    assert _dashboard_ok(client)

    admin = app.test_client()
    login(admin, ADMIN)
    with app.app_context():
        victim_id = User.query.filter_by(email="employee@test.example.com").first().id

    resp = admin.post(f"/users/{victim_id}/reset-password", data={
        "new_password": NEW_PASSWORD,
        "confirm_password": NEW_PASSWORD,
    }, follow_redirects=True)
    assert "Password reset" in resp.get_data(as_text=True)

    assert _logged_out(client)


def test_logout_all_revokes_others_but_keeps_current(app, client):
    login(client, ADMIN)
    other = app.test_client()
    login(other, ADMIN)

    resp = client.post("/profile/logout-all", follow_redirects=True)
    assert "All other sessions have been signed out." in resp.get_data(as_text=True)

    assert _dashboard_ok(client)     # current device stays signed in
    assert _logged_out(other)        # every other device is revoked


def test_idle_timeout_is_enforced(client):
    login(client, ADMIN)
    with client.session_transaction() as sess:
        sess[SESSION_SEEN_KEY] = 0
    assert _logged_out(client)


def test_absolute_timeout_is_enforced(client):
    login(client, ADMIN)
    with client.session_transaction() as sess:
        sess[SESSION_STARTED_KEY] = 0
    assert _logged_out(client)
