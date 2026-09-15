from pathlib import Path

from flask import Flask, render_template

from config import Config

from .extensions import csrf, db, limiter, login_manager, migrate
from .models import User
from .security_headers import register_security_headers


def create_app(overrides: dict | None = None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)
    register_security_headers(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_helpers():
        from .security import role_required
        return {"role_required": role_required}

    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def too_many_requests(error):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    from .routes.audit import audit_bp
    from .routes.auth import auth_bp
    from .routes.customers import customers_bp
    from .routes.dashboard import dashboard_bp
    from .routes.inventory import inventory_bp
    from .routes.products import products_bp
    from .routes.profile import profile_bp
    from .routes.sales import sales_bp
    from .routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(profile_bp)

    with app.app_context():
        db.create_all()

    return app
