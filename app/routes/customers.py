from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..forms import CustomerForm
from ..models import AuditLog, Customer
from ..security import encrypt_value, role_required, sanitize_text

customers_bp = Blueprint("customers", __name__, url_prefix="/customers")

@customers_bp.route("/")
@login_required
def index():
    customers = Customer.query.order_by(Customer.id.desc()).paginate(
        page=request.args.get("page", 1, type=int),
        per_page=current_app.config["PAGINATION_PER_PAGE"],
        error_out=False
    )
    return render_template("customers/index.html", customers=customers)

@customers_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager", "employee")
def create():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            name=sanitize_text(form.name.data, 120),
            email=form.email.data.lower().strip(),
            phone_encrypted=(
                encrypt_value(sanitize_text(form.phone.data, 30))
                if form.phone.data else None
            )
        )
        db.session.add(customer)
        db.session.flush()
        db.session.add(AuditLog(user_id=current_user.id, action="CUSTOMER_CREATED",
                                entity="Customer", entity_id=customer.id,
                                ip_address=request.remote_addr))
        db.session.commit()
        flash("Customer created.", "success")
        return redirect(url_for("customers.index"))
    return render_template("customers/form.html", form=form, title="Create Customer")

@customers_bp.route("/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager")
def edit(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        abort(404)
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        customer.name = sanitize_text(form.name.data, 120)
        customer.email = form.email.data.lower().strip()
        customer.phone_encrypted = (
            encrypt_value(sanitize_text(form.phone.data, 30))
            if form.phone.data else None
        )
        db.session.add(AuditLog(user_id=current_user.id, action="CUSTOMER_UPDATED",
                                entity="Customer", entity_id=customer.id,
                                ip_address=request.remote_addr))
        db.session.commit()
        flash("Customer updated.", "success")
        return redirect(url_for("customers.index"))
    return render_template("customers/form.html", form=form, title="Edit Customer")

@customers_bp.post("/<int:customer_id>/delete")
@login_required
@role_required("admin", "manager")
def delete(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        abort(404)
    try:
        db.session.delete(customer)
        db.session.commit()
        flash("Customer deleted.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Cannot delete customer with associated sales history.", "danger")
    return redirect(url_for("customers.index"))
