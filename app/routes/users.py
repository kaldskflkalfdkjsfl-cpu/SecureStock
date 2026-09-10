from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..forms import UserForm
from ..models import AuditLog, User
from ..security import hash_password, role_required, sanitize_text, validate_password

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
