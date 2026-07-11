import os
from datetime import timedelta


def _normalize_db_url(url: str) -> str:
    """Render/Heroku-style Postgres URLs come as postgres://; SQLAlchemy 1.4+
    requires the postgresql:// scheme. Normalize so DATABASE_URL can be
    pasted straight from the provider dashboard without edits."""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    APP_NAME = "MoveX"
    APP_TAGLINE = "Move Smarter. Deliver Faster."

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me-in-production")

    # --- Database ----------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(os.getcwd(), "instance", "movex.db"))
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Sessions / cookies --------------------------------------------------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True

    # --- CSRF ----------------------------------------------------------------
    WTF_CSRF_TIME_LIMIT = None  # tokens don't expire mid-session

    # --- Rate limiting ---------------------------------------------------------
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    # --- JWT (mobile / REST API) ------------------------------------------------
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))

    # --- Email (password reset / verification) -----------------------------------
    # No SMTP provider is wired up yet — MAIL_SUPPRESS_SEND keeps the app
    # functional in every environment by logging the message instead of
    # sending it until real credentials are supplied.
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@movex.app")
    MAIL_SUPPRESS_SEND = os.environ.get("MAIL_SUPPRESS_SEND", "true").lower() == "true"

    # --- Payments ------------------------------------------------------------
    # Wire real keys via environment variables once a Flutterwave/Paystack
    # merchant account exists — app/services/payments.py already reads from
    # these and falls back to a clear "not configured" error otherwise.
    FLUTTERWAVE_SECRET_KEY = os.environ.get("FLUTTERWAVE_SECRET_KEY")
    FLUTTERWAVE_PUBLIC_KEY = os.environ.get("FLUTTERWAVE_PUBLIC_KEY")
    PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY")
    PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY")

    # --- Maps ------------------------------------------------------------------
    OSM_NOMINATIM_URL = os.environ.get("OSM_NOMINATIM_URL", "https://nominatim.openstreetmap.org")
    OSRM_ROUTING_URL = os.environ.get("OSRM_ROUTING_URL", "https://router.project-osrm.org")


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
