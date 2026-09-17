from base64 import b64encode
from io import BytesIO

import qrcode
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user

from ..extensions import db, limiter
from ..forms import ChangePasswordForm
from ..models import AuditLog
from ..security import (
    bind_session,
    generate_totp_secret,
    hash_password,
    totp_provisioning_uri,
    validate_password,
    verify_password,
)

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

def _qr_png(uri: str) -> str:
    img = qrcode.make(uri, box_size=5, border=2)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + b64encode(buffer.getvalue()).decode()

@profile_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    pending_secret = session.get("tfa_pending_secret")

    if request.method == "POST":
        from ..security import verify_totp_code

        if request.form.get("disable"):
            if not current_user.two_factor_enabled:
                flash("Two-factor authentication is already disabled.", "warning")
                return redirect(url_for("profile.index"))
            if verify_totp_code(current_user.totp_secret, request.form.get("code", "")):
                current_user.totp_secret = None
                db.session.add(AuditLog(user_id=current_user.id, action="TFA_DISABLED",
                                        entity="User", entity_id=current_user.id,
                                        ip_address=request.remote_addr))
                db.session.commit()
                flash("Two-factor authentication disabled.", "info")
                return redirect(url_for("profile.index"))
            flash("Invalid verification code.", "danger")
            return redirect(url_for("profile.index"))

        if request.form.get("enable"):
            secret = generate_totp_secret()
            session["tfa_pending_secret"] = secret
            uri = totp_provisioning_uri(secret, current_user.email)
            db.session.add(AuditLog(user_id=current_user.id, action="TFA_ENROLL_STARTED",
                                    entity="User", entity_id=current_user.id,
                                    ip_address=request.remote_addr))
            db.session.commit()
            return render_template("profile/two_factor.html", qr_data=_qr_png(uri),
                                   provisioning_uri=uri, secret=secret, pending=True)

        secret = pending_secret or (
            current_user.totp_secret if current_user.two_factor_enabled else None
        )
        if not secret:
            flash("No pending two-factor setup.", "warning")
            return redirect(url_for("profile.index"))

        if request.form.get("confirm") and verify_totp_code(secret, request.form.get("code", "")):
            current_user.totp_secret = secret
            session.pop("tfa_pending_secret", None)
            db.session.add(AuditLog(user_id=current_user.id, action="TFA_ENABLED",
                                    entity="User", entity_id=current_user.id,
                                    ip_address=request.remote_addr))
            db.session.commit()
            flash("Two-factor authentication enabled.", "success")
            return redirect(url_for("profile.index"))

        flash("Invalid verification code.", "danger")
        return redirect(url_for("profile.index"))

    # GET: show setup screen if a pending secret exists
    if pending_secret and not current_user.two_factor_enabled:
        uri = totp_provisioning_uri(pending_secret, current_user.email)
        return render_template("profile/two_factor.html", qr_data=_qr_png(uri),
                               provisioning_uri=uri, secret=pending_secret, pending=True)

    return render_template("profile/index.html")

@profile_bp.route("/cancel", methods=["POST"])
@login_required
def cancel():
    session.pop("tfa_pending_secret", None)
    flash("Two-factor setup cancelled.", "info")
    return redirect(url_for("profile.index"))

@profile_bp.route("/password", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per minute")
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not verify_password(current_user.password_hash, form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return render_template("profile/password.html", form=form)

        if form.new_password.data != form.confirm_password.data:
            flash("New passwords do not match.", "danger")
            return render_template("profile/password.html", form=form)

        if not validate_password(form.new_password.data):
            flash(
                "Password must be 10+ chars and include upper, lower, digit and symbol.",
                "danger",
            )
            return render_template("profile/password.html", form=form)

        if form.new_password.data == form.current_password.data:
            flash("The new password must differ from the current password.", "danger")
            return render_template("profile/password.html", form=form)

        current_user.password_hash = hash_password(form.new_password.data)
        # Rotate the security stamp so every other session of this user is
        # invalidated immediately; the current device is rebound below.
        bind_session(current_user, rotate=True)
        db.session.add(AuditLog(user_id=current_user.id, action="PASSWORD_CHANGED",
                                entity="User", entity_id=current_user.id,
                                ip_address=request.remote_addr))
        db.session.commit()
        # Re-establish the current session with the freshly rotated stamp.
        login_user(current_user, remember=False, fresh=True)
        flash("Password changed successfully.", "success")
        return redirect(url_for("profile.index"))
    return render_template("profile/password.html", form=form)


@profile_bp.post("/logout-all")
@login_required
def logout_all():
    """Invalidate every other active session of the current user."""
    bind_session(current_user, rotate=True)
    db.session.add(AuditLog(user_id=current_user.id, action="SESSIONS_REVOKED",
                            entity="User", entity_id=current_user.id,
                            ip_address=request.remote_addr))
    db.session.commit()
    login_user(current_user, remember=False, fresh=True)
    flash("All other sessions have been signed out.", "success")
    return redirect(url_for("profile.index"))
