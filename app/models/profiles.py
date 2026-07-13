from datetime import datetime

from app.extensions import db


class PassengerProfile(db.Model):
    __tablename__ = "passenger_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    home_address = db.Column(db.String(255))
    rating_avg = db.Column(db.Float, default=5.0)
    total_trips = db.Column(db.Integer, default=0)
    referral_code = db.Column(db.String(16), unique=True)
    referred_by_code = db.Column(db.String(16))

    user = db.relationship("User", back_populates="passenger_profile")
    favorite_drivers = db.relationship(
        "FavoriteDriver", backref="passenger", lazy="dynamic", cascade="all, delete-orphan"
    )


class FavoriteDriver(db.Model):
    __tablename__ = "favorite_drivers"

    id = db.Column(db.Integer, primary_key=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey("passenger_profiles.id"), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("driver_profiles.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("passenger_id", "driver_id", name="uq_favorite_pair"),)


class DriverProfile(db.Model):
    __tablename__ = "driver_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)

    license_number = db.Column(db.String(64), unique=True, nullable=False)
    license_expiry = db.Column(db.Date)
    national_id_number = db.Column(db.String(64))

    is_approved = db.Column(db.Boolean, default=False, nullable=False, index=True)
    approval_status = db.Column(db.String(20), default="pending")  # pending / approved / rejected
    background_check_status = db.Column(db.String(20), default="pending")
    is_online = db.Column(db.Boolean, default=False, nullable=False, index=True)

    rating_avg = db.Column(db.Float, default=5.0)
    total_trips = db.Column(db.Integer, default=0)
    commission_rate = db.Column(db.Float, default=0.12)

    current_lat = db.Column(db.Float)
    current_lng = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="driver_profile")
    vehicles = db.relationship(
        "Vehicle", backref="driver", lazy="dynamic", cascade="all, delete-orphan"
    )


class VehicleType(db.Model):
    """Lookup table so pricing tiers (standard/comfort/xl) are configurable
    from the admin panel rather than hard-coded."""

    __tablename__ = "vehicle_types"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # standard, comfort, xl
    label = db.Column(db.String(50), nullable=False)
    base_fare = db.Column(db.Numeric(10, 2), nullable=False, default=2.0)
    per_km_rate = db.Column(db.Numeric(10, 2), nullable=False, default=0.8)
    per_minute_rate = db.Column(db.Numeric(10, 2), nullable=False, default=0.15)
    seats = db.Column(db.Integer, default=4)
    is_active = db.Column(db.Boolean, default=True)


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("driver_profiles.id"), nullable=False)
    vehicle_type_id = db.Column(db.Integer, db.ForeignKey("vehicle_types.id"))

    make = db.Column(db.String(60), nullable=False)
    model = db.Column(db.String(60), nullable=False)
    year = db.Column(db.Integer)
    color = db.Column(db.String(30))
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    insurance_expiry = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vehicle_type = db.relationship("VehicleType")


class BusinessProfile(db.Model):
    __tablename__ = "business_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)

    company_name = db.Column(db.String(150), nullable=False)
    registration_number = db.Column(db.String(80))
    industry = db.Column(db.String(80))
    billing_address = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="business_profile")
