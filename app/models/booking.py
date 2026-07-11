import enum
import secrets
from datetime import datetime

from app.extensions import db


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


def generate_booking_ref(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(4).upper()}"


class RideBooking(db.Model):
    __tablename__ = "ride_bookings"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(20), unique=True, default=lambda: generate_booking_ref("RIDE"))

    passenger_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("driver_profiles.id"), nullable=True)
    vehicle_type_id = db.Column(db.Integer, db.ForeignKey("vehicle_types.id"))

    pickup_address = db.Column(db.String(255), nullable=False)
    pickup_lat = db.Column(db.Float)
    pickup_lng = db.Column(db.Float)
    dropoff_address = db.Column(db.String(255), nullable=False)
    dropoff_lat = db.Column(db.Float)
    dropoff_lng = db.Column(db.Float)

    distance_km = db.Column(db.Float)
    eta_minutes = db.Column(db.Integer)
    fare_estimate_low = db.Column(db.Numeric(10, 2))
    fare_estimate_high = db.Column(db.Numeric(10, 2))
    final_fare = db.Column(db.Numeric(10, 2))

    promo_code_id = db.Column(db.Integer, db.ForeignKey("promo_codes.id"), nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False, index=True)
    cancellation_reason = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    passenger = db.relationship("User", foreign_keys=[passenger_id])
    driver = db.relationship("DriverProfile", foreign_keys=[driver_id])
    vehicle_type = db.relationship("VehicleType")
    trip = db.relationship("Trip", backref="ride_booking", uselist=False, cascade="all, delete-orphan")


class ParcelSize(str, enum.Enum):
    ENVELOPE = "envelope"
    PARCEL = "parcel"
    LARGE_BOX = "large_box"


class DeliveryBooking(db.Model):
    __tablename__ = "delivery_bookings"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(20), unique=True, default=lambda: generate_booking_ref("DLV"))

    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("driver_profiles.id"), nullable=True)

    pickup_address = db.Column(db.String(255), nullable=False)
    pickup_lat = db.Column(db.Float)
    pickup_lng = db.Column(db.Float)
    dropoff_address = db.Column(db.String(255), nullable=False)
    dropoff_lat = db.Column(db.Float)
    dropoff_lng = db.Column(db.Float)

    recipient_name = db.Column(db.String(120), nullable=False)
    recipient_phone = db.Column(db.String(32), nullable=False)
    parcel_size = db.Column(db.Enum(ParcelSize), default=ParcelSize.PARCEL, nullable=False)
    delivery_notes = db.Column(db.String(255))

    distance_km = db.Column(db.Float)
    fare_estimate_low = db.Column(db.Numeric(10, 2))
    fare_estimate_high = db.Column(db.Numeric(10, 2))
    final_fare = db.Column(db.Numeric(10, 2))

    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sender = db.relationship("User", foreign_keys=[sender_id])
    driver = db.relationship("DriverProfile", foreign_keys=[driver_id])
    trip = db.relationship(
        "Trip", backref="delivery_booking", uselist=False, cascade="all, delete-orphan"
    )


class Trip(db.Model):
    """Created once a driver accepts a booking; tracks the live/completed
    journey separately from the booking request itself."""

    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)
    ride_booking_id = db.Column(db.Integer, db.ForeignKey("ride_bookings.id"), nullable=True)
    delivery_booking_id = db.Column(db.Integer, db.ForeignKey("delivery_bookings.id"), nullable=True)

    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    actual_distance_km = db.Column(db.Float)
    actual_duration_minutes = db.Column(db.Integer)
    route_polyline = db.Column(db.Text)  # encoded polyline from the maps provider
    live_share_token = db.Column(db.String(48), unique=True, default=lambda: secrets.token_urlsafe(24))

    __table_args__ = (
        db.CheckConstraint(
            "(ride_booking_id IS NOT NULL) OR (delivery_booking_id IS NOT NULL)",
            name="ck_trip_has_booking",
        ),
    )
