import os
from datetime import timedelta


class ConfigError(RuntimeError):
    """Raised at startup when a required environment variable is missing.
    Fails loudly and immediately rather than falling back to a silent
    default that would mask a misconfigured deployment."""


def _normalize_db_url(url: str) -> str:
    """Render/Supabase/Heroku-style Postgres URLs come as postgres://;
    SQLAlchemy 2.x requires the postgresql:// scheme. Normalizing here means
    a connection string can be pasted straight from any provider's
    dashboard (Render, Supabase, or otherwise) with no edits."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def _require_database_url() -> str:
    """PostgreSQL (via Render's managed database, Supabase, or any other
    Postgres provider) is the only supported database — there is no SQLite
    fallback. This is intentional: SQLite's on-disk file doesn't survive a
    redeploy on most hosts (Render's free tier included), which silently
    "loses" all data the moment the instance restarts. Failing fast here
    with a clear message is far better than an app that boots, appears to
    work, and quietly discards everything on the next deploy."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ConfigError(
            "DATABASE_URL is not set. This app requires a PostgreSQL "
            "connection string (Render managed Postgres, Supabase, or any "
            "other Postgres provider) — SQLite is not supported. Set "
            "DATABASE_URL in your environment and restart."
        )
    return _normalize_db_url(url)


class Config:
    APP_NAME = "MoveX"
    APP_TAGLINE = "Move Smarter. Deliver Faster."

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me-in-production")

    # --- Database (PostgreSQL only — see _require_database_url) -----------
    SQLALCHEMY_DATABASE_URI = _require_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # drops stale connections instead of erroring on them
        "pool_recycle": 300,     # recycle connections every 5 min (managed Postgres often kills idle ones sooner)
    }

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

    # --- Supabase (optional) ----------------------------------------------------
    # Not required for the database itself — DATABASE_URL alone is enough to
    # use a Supabase Postgres instance via plain SQLAlchemy, which is what
    # this app does. These two are only needed if you later enable Supabase
    # Storage for file uploads (e.g. driver documents) instead of local disk.
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
