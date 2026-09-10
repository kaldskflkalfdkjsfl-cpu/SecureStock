from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import AuditLog, Product
from ..security import role_required

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")

@inventory_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()[:80]
    query = Product.query
    if q:
        escaped_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.filter(Product.name.ilike(f"%{escaped_q}%"))
    products = query.order_by(Product.quantity.asc()).paginate(
        page=request.args.get("page", 1, type=int),
        per_page=current_app.config["PAGINATION_PER_PAGE"],
        error_out=False
    )
    return render_template("inventory/index.html", products=products, q=q)

@inventory_bp.post("/<int:product_id>/adjust")
@login_required
@role_required("admin", "manager")
def adjust(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    try:
        amount = int(request.form.get("amount", "0"))
    except ValueError:
        flash("Invalid quantity.", "danger")
        return redirect(url_for("inventory.index"))
    if amount < -product.quantity:
        flash("Inventory cannot become negative.", "danger")
        return redirect(url_for("inventory.index"))
    product.quantity += amount
    db.session.add(AuditLog(user_id=current_user.id, action="INVENTORY_ADJUSTED",
                            entity="Product", entity_id=product.id,
                            ip_address=request.remote_addr))
    db.session.commit()
    flash("Inventory updated.", "success")
    return redirect(url_for("inventory.index"))
