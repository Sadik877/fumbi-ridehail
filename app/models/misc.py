import enum
from datetime import datetime

from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    icon = db.Column(db.String(40), default="bell")
    title = db.Column(db.String(150), nullable=False)
    body = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class Rating(db.Model):
    """A trip-specific star rating exchanged between the two parties of a
    completed ride or delivery (passenger <-> driver)."""

    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    ride_booking_id = db.Column(db.Integer, db.ForeignKey("ride_bookings.id"), nullable=True)
    delivery_booking_id = db.Column(db.Integer, db.ForeignKey("delivery_bookings.id"), nullable=True)

    rater_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ratee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    stars = db.Column(db.SmallInteger, nullable=False)
    comment = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.CheckConstraint("stars >= 1 AND stars <= 5", name="ck_rating_stars_range"),)


class Review(db.Model):
    """Public-facing testimonial/review shown on the marketing site,
    distinct from per-trip Ratings."""

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150))
    body = db.Column(db.String(1000), nullable=False)
    stars = db.Column(db.SmallInteger, nullable=False, default=5)
    is_published = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DiscountType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class PromoCode(db.Model):
    __tablename__ = "promo_codes"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    discount_type = db.Column(db.Enum(DiscountType), nullable=False, default=DiscountType.PERCENTAGE)
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    min_fare = db.Column(db.Numeric(10, 2), default=0)
    max_uses = db.Column(db.Integer)
    times_used = db.Column(db.Integer, default=0)
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def is_valid(self, now=None) -> bool:
        now = now or datetime.utcnow()
        if not self.is_active:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses and self.times_used >= self.max_uses:
            return False
        return True


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportTicket(db.Model):
    __tablename__ = "support_tickets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(60), default="General")
    status = db.Column(db.Enum(TicketStatus), default=TicketStatus.OPEN, index=True)
    priority = db.Column(db.String(20), default="normal")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SavedLocation(db.Model):
    __tablename__ = "saved_locations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    label = db.Column(db.String(60), nullable=False)  # e.g. "Home", "Office"
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmergencyContact(db.Model):
    __tablename__ = "emergency_contacts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(32), nullable=False)
    relationship_label = db.Column(db.String(60))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
