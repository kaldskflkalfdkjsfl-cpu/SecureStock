from decimal import Decimal

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import SaleForm, UploadForm
from ..models import AuditLog, Customer, Product, Sale, SaleItem
from ..security import role_required, safe_upload_path, validate_upload_file

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")

@sales_bp.route("/")
@login_required
def index():
    query = Sale.query
    if current_user.role == "employee":
        query = query.filter(Sale.user_id == current_user.id)
    sales = query.order_by(Sale.id.desc()).paginate(
        page=request.args.get("page", 1, type=int),
        per_page=current_app.config.get("PAGINATION_PER_PAGE", 20),
        error_out=False
    )
    return render_template("sales/index.html", sales=sales)

@sales_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager", "employee")
def create():
    form = SaleForm()
    form.customer_id.choices = [
        (c.id, c.name) for c in Customer.query.order_by(Customer.name).all()
    ]
    form.product_id.choices = [
        (p.id, f"{p.name} (stock: {p.quantity})")
        for p in Product.query.order_by(Product.name).all()
    ]

    if form.validate_on_submit():
        customer = db.session.get(Customer, form.customer_id.data)
        product = db.session.get(Product, form.product_id.data)

        if not customer or not product:
            flash("Invalid customer or product.", "danger")
            return render_template("sales/form.html", form=form)

        quantity = form.quantity.data
        if quantity > product.quantity:
            flash("Insufficient stock.", "danger")
            return render_template("sales/form.html", form=form)

        # Real database transaction: sale + item + inventory update.
        try:
            total = Decimal(product.price) * quantity
            sale = Sale(customer_id=customer.id, user_id=current_user.id, total=total)
            db.session.add(sale)
            db.session.flush()

            item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price
            )
            product.quantity -= quantity
            db.session.add(item)
            db.session.add(AuditLog(
                user_id=current_user.id,
                action="SALE_CREATED",
                entity="Sale",
                entity_id=sale.id,
                ip_address=request.remote_addr
            ))
            db.session.commit()
            flash(f"Sale #{sale.id} created successfully.", "success")
            return redirect(url_for("sales.detail", sale_id=sale.id))
        except Exception:
            db.session.rollback()
            flash("The transaction failed and was rolled back.", "danger")

    return render_template("sales/form.html", form=form)

@sales_bp.route("/<int:sale_id>")
@login_required
def detail(sale_id):
    sale = db.session.get(Sale, sale_id)
    if not sale:
        abort(404)

    # IDOR defense: employees can see only sales they created.
    if current_user.role == "employee" and sale.user_id != current_user.id:
        abort(403)

    upload_form = UploadForm()
    return render_template("sales/detail.html", sale=sale, upload_form=upload_form)

@sales_bp.post("/<int:sale_id>/upload")
@login_required
def upload(sale_id):
    sale = db.session.get(Sale, sale_id)
    if not sale:
        abort(404)

    if current_user.role == "employee" and sale.user_id != current_user.id:
        abort(403)

    form = UploadForm()
    if form.validate_on_submit() and form.file.data:
        try:
            filename = validate_upload_file(form.file.data.filename, form.file.data.stream)
            destination = safe_upload_path(filename)
            form.file.data.save(destination)
            db.session.add(AuditLog(user_id=current_user.id, action="UPLOAD_ATTACHMENT",
                                    entity="Sale", entity_id=sale_id,
                                    ip_address=request.remote_addr))
            db.session.commit()
            flash("Attachment uploaded safely.", "success")
        except (ValueError, OSError):
            flash("Invalid, unsafe or disallowed file.", "danger")
    return redirect(url_for("sales.detail", sale_id=sale_id))

@sales_bp.route("/uploads/<path:filename>")
@login_required
@role_required("admin", "manager")
def uploaded_file(filename):
    # Path traversal defense: safe_upload_path validates the final resolved path.
    try:
        path = safe_upload_path(filename)
        if not path.exists():
            abort(404)
        return send_from_directory(current_app.config["UPLOAD_FOLDER"], path.name)
    except ValueError:
        abort(403)
