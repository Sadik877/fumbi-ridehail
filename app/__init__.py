import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template

from app.config import config_map
from app.extensions import db, migrate, login_manager, csrf, limiter, mail


def create_app(config_name: str = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "default")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    os.makedirs(app.instance_path, exist_ok=True)

    # --- Extensions ------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Blueprints --------------------------------------------------------
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.booking import booking_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.driver import driver_bp
    from app.routes.business import business_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.routes.seo import seo_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(seo_bp)

    # The JSON API is exempted from CSRF (it authenticates via JWT bearer
    # tokens, not session cookies) but keeps rate limiting.
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp)

    # --- Template globals ----------------------------------------------------
    @app.context_processor
    def inject_globals():
        return {
            "app_name": app.config["APP_NAME"],
            "app_tagline": app.config["APP_TAGLINE"],
        }

    @app.template_filter("merge_query")
    def merge_query(args_dict, **overrides):
        """Used by partials/pagination.html to build a "next/previous page"
        link that preserves existing filters (search terms, role filter,
        etc.) while only changing the `page` parameter."""
        from urllib.parse import urlencode

        merged = {**args_dict, **overrides}
        return urlencode(merged)

    # --- Security headers ------------------------------------------------------
    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(self), camera=(), microphone=()")
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
            )
        return response

    # --- Error handlers ----------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(429)
    def rate_limited(e):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error")
        return render_template("errors/500.html"), 500

    # --- Logging -------------------------------------------------------------
    if not app.debug and not app.testing:
        os.makedirs("logs", exist_ok=True)
        file_handler = RotatingFileHandler("logs/movex.log", maxBytes=1_000_000, backupCount=5)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s [in %(pathname)s:%(lineno)d]")
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

    # --- CLI commands --------------------------------------------------------
    register_cli(app)

    return app


def register_cli(app: Flask):
    @app.cli.command("init-db")
    def init_db():
        """Create all tables directly from the current models.

        This is a pragmatic bootstrap for environments without shell access
        (e.g. Render's free tier) where running `flask db init/migrate` isn't
        practical. It's equivalent to a first migration's "upgrade" for a
        brand-new, empty database. Once you have a local dev environment
        with git access, switch to real Flask-Migrate migrations for any
        schema changes after this point — repeatedly calling this command
        is safe (create_all only creates missing tables, it never drops or
        alters existing ones) but it won't apply ALTER TABLE-style changes.
        """
        db.create_all()
        print("Tables created (or already existed).")

    @app.cli.command("seed-db")
    def seed_db():
        """Populate vehicle types, an admin account, and sample public reviews."""
        from app.seed import run_seed

        run_seed()
        print("Database seeded.")
