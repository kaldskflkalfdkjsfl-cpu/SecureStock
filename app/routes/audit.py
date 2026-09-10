from flask import Blueprint, current_app, render_template, request
from flask_login import login_required

from ..models import AuditLog
from ..security import role_required

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")

@audit_bp.route("/")
@login_required
@role_required("admin")
def index():
    action = (request.args.get("action") or "").strip()[:100]
    query = AuditLog.query
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.order_by(AuditLog.id.desc()).paginate(
        page=request.args.get("page", 1, type=int),
        per_page=current_app.config["PAGINATION_PER_PAGE"],
        error_out=False
    )
    return render_template("audit/index.html", logs=logs, action=action)
