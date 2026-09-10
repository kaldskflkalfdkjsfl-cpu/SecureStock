from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import ProductForm
from ..models import AuditLog, Product
from ..security import role_required, sanitize_text

products_bp = Blueprint("products", __name__, url_prefix="/products")

@products_bp.route("/")
@login_required
def index():
    q = sanitize_text(request.args.get("q", ""), 80)
    query = Product.query
    if q:
        escaped_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.filter(Product.name.ilike(f"%{escaped_q}%"))
    products = query.order_by(Product.id.desc()).paginate(
        page=request.args.get("page", 1, type=int),
        per_page=current_app.config["PAGINATION_PER_PAGE"],
        error_out=False
    )
    return render_template("products/index.html", products=products, q=q)

@products_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager")
def create():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=sanitize_text(form.name.data, 120),
            description=sanitize_text(form.description.data, 500),
            price=form.price.data,
            quantity=form.quantity.data,
            low_stock_threshold=form.low_stock_threshold.data
        )
        db.session.add(product)
        db.session.flush()
        db.session.add(AuditLog(user_id=current_user.id, action="PRODUCT_CREATED",
                                entity="Product", entity_id=product.id,
                                ip_address=request.remote_addr))
        db.session.commit()
        flash("Product created.", "success")
        return redirect(url_for("products.index"))
    return render_template("products/form.html", form=form, title="Create Product")

@products_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager")
def edit(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = sanitize_text(form.name.data, 120)
        product.description = sanitize_text(form.description.data, 500)
        product.price = form.price.data
        product.quantity = form.quantity.data
        product.low_stock_threshold = form.low_stock_threshold.data
        db.session.add(AuditLog(user_id=current_user.id, action="PRODUCT_UPDATED",
                                entity="Product", entity_id=product.id,
                                ip_address=request.remote_addr))
        db.session.commit()
        flash("Product updated.", "success")
        return redirect(url_for("products.index"))
    return render_template("products/form.html", form=form, title="Edit Product")

@products_bp.post("/<int:product_id>/delete")
@login_required
@role_required("admin", "manager")
def delete(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "success")
    return redirect(url_for("products.index"))
