import os


class Config:
    """Base configuration. Real secrets should come from environment
    variables / a secrets manager in production — never hard-code them."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")
    APP_NAME = "Fumbi"
    APP_TAGLINE = "Move. Send. Arrive."

    # --- Placeholders for future backend integration -------------------
    # SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    # REDIS_URL = os.environ.get("REDIS_URL")
    # PAYMENT_PROVIDER_KEY = os.environ.get("PAYMENT_PROVIDER_KEY")
    # MAPS_API_KEY = os.environ.get("MAPS_API_KEY")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
