"""
Flask extension instances, created here (uninitialized) and bound to the
app in create_app() via .init_app(). Importing from this module instead of
instantiating extensions inside __init__.py avoids circular imports between
models, blueprints, and the app factory.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])
mail = Mail()

login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
