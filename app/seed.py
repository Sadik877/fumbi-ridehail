"""
Run via: flask seed-db

Populates the reference data the app needs to function (vehicle pricing
tiers) plus one admin account and a handful of published reviews so the
landing page isn't empty on a fresh database. No fake passengers, drivers,
or bookings are created — those come from real registrations.
"""
import os

from app.extensions import db
from app.models import User, UserRole, VehicleType, Review, PromoCode, DiscountType, Wallet


def run_seed():
    _seed_vehicle_types()
    _seed_admin()
    _seed_reviews()
    _seed_promo()
    db.session.commit()


def _seed_vehicle_types():
    defaults = [
        {"code": "standard", "label": "Standard", "base_fare": 500, "per_km_rate": 120, "per_minute_rate": 15, "seats": 4},
        {"code": "comfort", "label": "Comfort", "base_fare": 800, "per_km_rate": 180, "per_minute_rate": 25, "seats": 4},
        {"code": "xl", "label": "XL", "base_fare": 1200, "per_km_rate": 220, "per_minute_rate": 30, "seats": 6},
    ]
    for entry in defaults:
        if not VehicleType.query.filter_by(code=entry["code"]).first():
            db.session.add(VehicleType(**entry))


def _seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@movex.app")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if User.query.filter_by(email=admin_email).first():
        return
    if not admin_password:
        print(
            "WARNING: ADMIN_PASSWORD not set — skipping admin account creation. "
            "Set ADMIN_EMAIL and ADMIN_PASSWORD env vars and re-run `flask seed-db`."
        )
        return
    admin = User(
        full_name="MoveX Admin",
        email=admin_email,
        phone=os.environ.get("ADMIN_PHONE", "+2340000000000"),
        role=UserRole.ADMIN,
        is_email_verified=True,
        is_phone_verified=True,
    )
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.flush()
    db.session.add(Wallet(user_id=admin.id))


def _seed_reviews():
    if Review.query.first():
        return
    # Reviews are attached to the admin account as the record owner; in
    # production these would be created by real users after a completed trip.
    admin = User.query.filter_by(role=UserRole.ADMIN).first()
    if not admin:
        return
    samples = [
        ("Reliable, every time", "I schedule my airport rides three days out now. It's never once been late.", 5),
        ("Delivery was instant", "Sent a parcel across town before lunch — it was signed for before I'd finished my coffee.", 5),
        ("Great for drivers too", "Driving full-time on MoveX paid off my car loan in under a year.", 5),
    ]
    for title, body, stars in samples:
        db.session.add(Review(user_id=admin.id, title=title, body=body, stars=stars, is_published=True))


def _seed_promo():
    if PromoCode.query.filter_by(code="MOVEX10").first():
        return
    db.session.add(
        PromoCode(
            code="MOVEX10",
            description="10% off your next ride",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=10,
            min_fare=0,
            max_uses=None,
            is_active=True,
        )
    )
