import enum
from datetime import datetime, timedelta

from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class UserRole(str, enum.Enum):
    PASSENGER = "passenger"
    DRIVER = "driver"
    BUSINESS = "business"
    ADMIN = "admin"


class User(UserMixin, db.Model):
    """
    Base account record for every actor on the platform. Role-specific data
    lives in PassengerProfile / DriverProfile / BusinessProfile (1:1),
    keeping this table lean and shared across all account types.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.PASSENGER, index=True)
    city = db.Column(db.String(80))
    avatar_url = db.Column(db.String(255))

    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_phone_verified = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)

    # --- Relationships ---------------------------------------------------
    # The four 1:1 relationships below use explicit back_populates (rather
    # than backref) so both sides of each relationship are declared and
    # visible directly in each model file.
    passenger_profile = db.relationship(
        "PassengerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    driver_profile = db.relationship(
        "DriverProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    business_profile = db.relationship(
        "BusinessProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    wallet = db.relationship(
        "Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    saved_locations = db.relationship(
        "SavedLocation", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    emergency_contacts = db.relationship(
        "EmergencyContact", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    support_tickets = db.relationship(
        "SupportTicket", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    # --- Password ----------------------------------------------------------
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    # --- Flask-Login required properties -----------------------------------
    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self.is_active_account

    # --- Stateless tokens (email verification / password reset) ------------
    # Uses itsdangerous rather than a DB-backed token table: tokens are
    # self-expiring and signed with SECRET_KEY, which is sufficient for a
    # single-use, short-lived link and avoids an extra table + cleanup job.
    @staticmethod
    def _serializer() -> URLSafeTimedSerializer:
        return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    def get_reset_token(self) -> str:
        return self._serializer().dumps({"user_id": self.id, "purpose": "reset"})

    def get_email_verification_token(self) -> str:
        return self._serializer().dumps({"user_id": self.id, "purpose": "verify_email"})

    @staticmethod
    def verify_token(token: str, purpose: str, max_age_seconds: int = 3600):
        try:
            data = User._serializer().loads(token, max_age=max_age_seconds)
        except (BadSignature, SignatureExpired):
            return None
        if data.get("purpose") != purpose:
            return None
        return User.query.get(data.get("user_id"))

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"
