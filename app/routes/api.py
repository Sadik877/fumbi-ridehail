"""
JSON REST API for the Android/iOS apps. Authenticated with JWT bearer
tokens (see app/utils/jwt_auth.py) rather than session cookies, so it's
exempted from CSRF in the app factory — CSRF protection exists specifically
to stop browsers from silently attaching cookies to forged requests, which
doesn't apply to an explicit Authorization header a mobile client sets
itself.
"""
from flask import Blueprint, request, jsonify, g

from app.extensions import db, limiter
from app.models import (
    User, UserRole, PassengerProfile, Wallet, VehicleType, RideBooking,
    DeliveryBooking, BookingStatus,
)
from app.services import maps, pricing
from app.utils.jwt_auth import issue_token, jwt_required

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.route("/auth/register", methods=["POST"])
@limiter.limit("10 per minute")
def api_register():
    data = request.get_json(silent=True) or {}
    required = ["full_name", "email", "phone", "password"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if User.query.filter((User.email == data["email"].lower()) | (User.phone == data["phone"])).first():
        return jsonify({"error": "Email or phone already registered"}), 409

    user = User(
        full_name=data["full_name"], email=data["email"].lower(), phone=data["phone"],
        role=UserRole.PASSENGER,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()
    db.session.add(PassengerProfile(user_id=user.id))
    db.session.add(Wallet(user_id=user.id))
    db.session.commit()

    return jsonify({"token": issue_token(user), "user": _user_json(user)}), 201


@api_bp.route("/auth/login", methods=["POST"])
@limiter.limit("15 per minute")
def api_login():
    data = request.get_json(silent=True) or {}
    identifier, password = data.get("identifier"), data.get("password")
    if not identifier or not password:
        return jsonify({"error": "identifier and password are required"}), 400

    user = User.query.filter((User.email == identifier.lower()) | (User.phone == identifier)).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    if not user.is_active_account:
        return jsonify({"error": "Account suspended"}), 403

    return jsonify({"token": issue_token(user), "user": _user_json(user)})


@api_bp.route("/me")
@jwt_required
def api_me():
    return jsonify(_user_json(g.current_api_user))


@api_bp.route("/rides/estimate", methods=["POST"])
@limiter.limit("30 per minute")
def api_ride_estimate():
    data = request.get_json(silent=True) or {}
    vehicle_type = VehicleType.query.filter_by(code=data.get("tier", "standard"), is_active=True).first()
    if not vehicle_type:
        return jsonify({"error": "Unknown vehicle tier"}), 400

    distance_km, duration_minutes = 6.0, 18.0
    pickup, dropoff = data.get("pickup_address"), data.get("dropoff_address")
    if pickup and dropoff:
        p, d = maps.geocode(pickup), maps.geocode(dropoff)
        if p and d:
            route = maps.get_route(p["lat"], p["lng"], d["lat"], d["lng"])
            if route:
                distance_km, duration_minutes = route["distance_km"], route["duration_minutes"]
            else:
                distance_km = pricing.haversine_km(p["lat"], p["lng"], d["lat"], d["lng"])
                duration_minutes = pricing.estimate_duration_minutes(distance_km)

    low, high = pricing.estimate_fare(
        distance_km, duration_minutes, vehicle_type.base_fare, vehicle_type.per_km_rate, vehicle_type.per_minute_rate
    )
    return jsonify({"fare_low": low, "fare_high": high, "distance_km": distance_km, "eta_minutes": round(duration_minutes)})


@api_bp.route("/rides", methods=["GET", "POST"])
@jwt_required
def api_rides():
    user = g.current_api_user
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        required = ["pickup_address", "dropoff_address"]
        if any(not data.get(f) for f in required):
            return jsonify({"error": "pickup_address and dropoff_address are required"}), 400

        vehicle_type = VehicleType.query.filter_by(code=data.get("vehicle_type", "standard")).first()
        booking = RideBooking(
            passenger_id=user.id,
            vehicle_type_id=vehicle_type.id if vehicle_type else None,
            pickup_address=data["pickup_address"],
            dropoff_address=data["dropoff_address"],
        )
        db.session.add(booking)
        db.session.commit()
        return jsonify(_ride_json(booking)), 201

    rides = RideBooking.query.filter_by(passenger_id=user.id).order_by(RideBooking.created_at.desc()).limit(50).all()
    return jsonify([_ride_json(r) for r in rides])


@api_bp.route("/rides/<int:ride_id>")
@jwt_required
def api_ride_detail(ride_id):
    ride = RideBooking.query.filter_by(id=ride_id, passenger_id=g.current_api_user.id).first_or_404()
    return jsonify(_ride_json(ride))


def _user_json(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role.value,
        "city": user.city,
        "is_email_verified": user.is_email_verified,
    }


def _ride_json(ride: RideBooking) -> dict:
    return {
        "id": ride.id,
        "reference": ride.reference,
        "pickup_address": ride.pickup_address,
        "dropoff_address": ride.dropoff_address,
        "status": ride.status.value,
        "fare_estimate_low": float(ride.fare_estimate_low or 0),
        "fare_estimate_high": float(ride.fare_estimate_high or 0),
        "final_fare": float(ride.final_fare) if ride.final_fare else None,
        "created_at": ride.created_at.isoformat(),
    }
