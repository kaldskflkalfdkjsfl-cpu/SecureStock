from flask import Blueprint, render_template
from flask_login import login_required

from ..models import AuditLog, Customer, Product, Sale, User

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/")
@login_required
def index():
    return render_template(
        "dashboard.html",
        product_count=Product.query.count(),
        customer_count=Customer.query.count(),
        sale_count=Sale.query.count(),
        user_count=User.query.count(),
        low_stock=Product.query.filter(Product.quantity <= Product.low_stock_threshold).all(),
        recent_logs=AuditLog.query.order_by(AuditLog.id.desc()).limit(6).all()
    )
