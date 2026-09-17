from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..forms import ResetPasswordForm, UserForm
from ..models import AuditLog, User
from ..security import (
    hash_password,
    new_session_token,
    role_required,
    sanitize_text,
    validate_password,
)

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("/")
@login_required
@role_required("admin")
def index():
    users = User.query.order_by(User.id.desc()).paginate(
        page=request.args.get("page", 1, type=int),
        per_page=current_app.config["PAGINATION_PER_PAGE"],
        error_out=False
    )
    return render_template("users/index.html", users=users)

@users_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create():
    form = UserForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return render_template("users/form.html", form=form, title="Create User")

        if not validate_password(form.password.data):
            flash(
                "Password must be 10+ chars and include upper, lower, digit and symbol.",
                "danger",
            )
            return render_template("users/form.html", form=form, title="Create User")

        user = User(
            name=sanitize_text(form.name.data, 120),
            email=email,
            role=form.role.data,
            password_hash=hash_password(form.password.data),
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(AuditLog(user_id=current_user.id,
                                action="USER_CREATED", entity="User", entity_id=user.id,
                                ip_address=request.remote_addr))
        db.session.commit()
        flash("User created.", "success")
        return redirect(url_for("users.index"))
    return render_template("users/form.html", form=form, title="Create User")

@users_bp.post("/<int:user_id>/delete")
@login_required
@role_required("admin")
def delete(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot delete yourself.", "danger")
        return redirect(url_for("users.index"))
    try:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Cannot delete user with associated sales or activity logs.", "danger")
    return redirect(url_for("users.index"))

@users_bp.route("/<int:user_id>/reset-password", methods=["GET", "POST"])
@login_required
@role_required("admin")
def reset_password(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if form.new_password.data != form.confirm_password.data:
            flash("New passwords do not match.", "danger")
            return render_template("users/reset_password.html", form=form, user=user)

        if not validate_password(form.new_password.data):
            flash(
                "Password must be 10+ chars and include upper, lower, digit and symbol.",
                "danger",
            )
            return render_template("users/reset_password.html", form=form, user=user)

        user.password_hash = hash_password(form.new_password.data)
        # A password reset also clears any lockout so the user can log in again.
        user.failed_attempts = 0
        user.locked_until = None
        # Rotate the security stamp: all of the target user's sessions are
        # invalidated so a compromised session cannot survive a reset.
        user.session_token = new_session_token()
        db.session.add(AuditLog(user_id=current_user.id, action="PASSWORD_RESET",
                                entity="User", entity_id=user.id,
                                ip_address=request.remote_addr))
        db.session.commit()
        flash(f"Password reset for {user.email}.", "success")
        return redirect(url_for("users.index"))
    return render_template("users/reset_password.html", form=form, user=user)
