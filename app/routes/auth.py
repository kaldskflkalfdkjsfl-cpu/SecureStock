from datetime import UTC, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from ..extensions import db, limiter
from ..forms import LoginForm, TotpForm
from ..models import AuditLog, User
from ..security import verify_password, verify_totp_code

auth_bp = Blueprint("auth", __name__)

DUMMY_HASH = (
    "scrypt:32768:8:1$XhOFpfsLluAtqKDD$"
    "b7537b3249e85c42610d411ecd03420783654a3ef5554c6d4e67da597f7b71c7f43b92f3761870dfb5c7c44a202ba5184a2d4e7927b6c5398bcdfc22f00899b5"
)

@auth_bp.route("/", methods=["GET"])
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        if user and user.is_locked():
            db.session.add(AuditLog(user_id=user.id, action="LOGIN_BLOCKED_LOCKED",
                                    entity="User", entity_id=user.id,
                                    ip_address=request.remote_addr))
            db.session.commit()
            flash("Invalid credentials or account temporarily locked.", "danger")
            return render_template("auth/login.html", form=form)

        # Constant-time comparison: verify against a dummy hash when the
        # account does not exist so response timing does not leak account existence.
        password_ok = verify_password(
            user.password_hash if user else DUMMY_HASH,
            form.password.data
        )

        if user and password_ok:
            user.failed_attempts = 0
            user.locked_until = None
            db.session.add(AuditLog(user_id=user.id, action="LOGIN_SUCCESS",
                                    entity="User", entity_id=user.id,
                                    ip_address=request.remote_addr))
            db.session.commit()

            if user.two_factor_enabled:
                # Two-step login: password verified, now require TOTP code.
                session.clear()
                session["tfa_user_id"] = user.id
                session["tfa_email"] = user.email
                session.permanent = True
                return redirect(url_for("auth.verify_2fa"))

            session.clear()
            login_user(user, remember=False, fresh=True)
            session.permanent = True
            return redirect(url_for("dashboard.index"))

        if user:
            user.failed_attempts += 1
            if user.failed_attempts >= 3:
                user.locked_until = datetime.now(UTC) + timedelta(minutes=15)
                user.failed_attempts = 0
            db.session.add(AuditLog(user_id=user.id, action="LOGIN_FAILED",
                                    entity="User", entity_id=user.id,
                                    ip_address=request.remote_addr))
        else:
            # Log brute-force attempts against unknown accounts too.
            db.session.add(AuditLog(user_id=None, action="LOGIN_FAILED_UNKNOWN",
                                    entity="User", entity_id=None,
                                    ip_address=request.remote_addr))
        db.session.commit()

        flash("Invalid credentials.", "danger")

    return render_template("auth/login.html", form=form)

@auth_bp.route("/login/2fa", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def verify_2fa():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    tfa_user_id = session.get("tfa_user_id")
    if not tfa_user_id:
        # No pending two-step login: send the user to the normal login page.
        return redirect(url_for("auth.login"))

    user = db.session.get(User, tfa_user_id)
    if not user or not user.two_factor_enabled:
        session.clear()
        return redirect(url_for("auth.login"))

    form = TotpForm()
    if form.validate_on_submit():
        if verify_totp_code(user.totp_secret, form.code.data):
            db.session.add(AuditLog(user_id=user.id, action="TOTP_VERIFIED",
                                    entity="User", entity_id=user.id,
                                    ip_address=request.remote_addr))
            db.session.commit()
            session.clear()
            login_user(user, remember=False, fresh=True)
            session.permanent = True
            return redirect(url_for("dashboard.index"))

        db.session.add(AuditLog(user_id=user.id, action="TOTP_FAILED",
                                entity="User", entity_id=user.id,
                                ip_address=request.remote_addr))
        db.session.commit()
        flash("Invalid verification code.", "danger")

    return render_template("auth/2fa.html", form=form, email=user.email)

@auth_bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        db.session.add(AuditLog(user_id=current_user.id, action="LOGOUT",
                                entity="User", entity_id=current_user.id,
                                ip_address=request.remote_addr))
        db.session.commit()
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))
