from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app.extensions import db, limiter
from app.forms import RideBookingForm, DeliveryBookingForm
from app.models import (
    RideBooking, DeliveryBooking, VehicleType, BookingStatus, UserRole, ParcelSize, DriverProfile,
)
from app.services import maps, pricing
from app.services.notifications import notify

booking_bp = Blueprint("booking", __name__, url_prefix="/book")


@booking_bp.route("/ride", methods=["GET", "POST"])
@login_required
def ride():
    form = RideBookingForm()
    vehicle_types = VehicleType.query.filter_by(is_active=True).all()

    if form.validate_on_submit():
        booking = _create_ride_booking(form)
        flash("Ride requested — we're matching you with a nearby driver.", "success")
        return redirect(url_for("booking.history"))

    return render_template("booking/ride.html", form=form, vehicle_types=vehicle_types)


@booking_bp.route("/delivery", methods=["GET", "POST"])
@login_required
def delivery():
    form = DeliveryBookingForm()

    if form.validate_on_submit():
        _create_delivery_booking(form)
        flash("Delivery requested — we're matching you with a courier.", "success")
        return redirect(url_for("booking.history"))

    return render_template("booking/delivery.html", form=form)


@booking_bp.route("/history")
@login_required
def history():
    status = request.args.get("status", "all")

    ride_query = RideBooking.query.options(
        joinedload(RideBooking.driver).joinedload(DriverProfile.user)
    ).filter_by(passenger_id=current_user.id)
    delivery_query = DeliveryBooking.query.options(
        joinedload(DeliveryBooking.driver).joinedload(DriverProfile.user)
    ).filter_by(sender_id=current_user.id)
    if status != "all":
        ride_query = ride_query.filter_by(status=BookingStatus(status))
        delivery_query = delivery_query.filter_by(status=BookingStatus(status))

    rides = [{"kind": "ride", "obj": r} for r in ride_query.order_by(RideBooking.created_at.desc()).all()]
    deliveries = [{"kind": "delivery", "obj": d} for d in delivery_query.order_by(DeliveryBooking.created_at.desc()).all()]
    bookings = sorted(rides + deliveries, key=lambda b: b["obj"].created_at, reverse=True)

    return render_template("booking/history.html", bookings=bookings, active_status=status, active="history")


@booking_bp.route("/cancel/<kind>/<int:booking_id>", methods=["POST"])
@login_required
def cancel(kind, booking_id):
    model = RideBooking if kind == "ride" else DeliveryBooking
    owner_field = "passenger_id" if kind == "ride" else "sender_id"
    booking = model.query.get_or_404(booking_id)

    if getattr(booking, owner_field) != current_user.id:
        flash("You can only cancel your own bookings.", "error")
        return redirect(url_for("booking.history"))
    if booking.status in (BookingStatus.COMPLETED, BookingStatus.CANCELLED):
        flash("This booking can no longer be cancelled.", "error")
        return redirect(url_for("booking.history"))

    booking.status = BookingStatus.CANCELLED
    booking.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Booking cancelled.", "success")
    return redirect(url_for("booking.history"))


@booking_bp.route("/estimate", methods=["POST"])
@limiter.limit("30 per minute")
def estimate():
    """Real fare estimate: geocodes both addresses (OSM Nominatim), routes
    between them (OSRM), and prices against the vehicle tier's rate card.
    Falls back to a straight-line (haversine) distance estimate if the
    routing engine can't be reached, so booking never hard-fails on a
    third-party outage."""
    payload = request.get_json(silent=True) or {}
    pickup = payload.get("pickup_address", "")
    dropoff = payload.get("dropoff_address", "")
    tier_code = payload.get("tier", "standard")

    vehicle_type = VehicleType.query.filter_by(code=tier_code, is_active=True).first()
    if not vehicle_type:
        return jsonify({"error": "Unknown vehicle tier"}), 400

    distance_km, duration_minutes = 6.0, 18.0  # sane defaults if geocoding is unavailable
    if pickup and dropoff:
        pickup_geo = maps.geocode(pickup)
        dropoff_geo = maps.geocode(dropoff)
        if pickup_geo and dropoff_geo:
            route = maps.get_route(pickup_geo["lat"], pickup_geo["lng"], dropoff_geo["lat"], dropoff_geo["lng"])
            if route:
                distance_km, duration_minutes = route["distance_km"], route["duration_minutes"]
            else:
                distance_km = pricing.haversine_km(
                    pickup_geo["lat"], pickup_geo["lng"], dropoff_geo["lat"], dropoff_geo["lng"]
                )
                duration_minutes = pricing.estimate_duration_minutes(distance_km)

    low, high = pricing.estimate_fare(
        distance_km, duration_minutes, vehicle_type.base_fare, vehicle_type.per_km_rate, vehicle_type.per_minute_rate
    )
    return jsonify(
        {
            "fare_low": low,
            "fare_high": high,
            "distance_km": round(distance_km, 2),
            "eta_minutes": round(duration_minutes),
            "currency": "NGN",
        }
    )


@booking_bp.route("/rate/<kind>/<int:booking_id>", methods=["POST"])
@login_required
def rate(kind, booking_id):
    from app.models import Rating

    model = RideBooking if kind == "ride" else DeliveryBooking
    owner_field = "passenger_id" if kind == "ride" else "sender_id"
    booking = model.query.get_or_404(booking_id)

    if getattr(booking, owner_field) != current_user.id:
        flash("You can only rate your own trips.", "error")
        return redirect(url_for("booking.history"))
    if booking.status != BookingStatus.COMPLETED or not booking.driver:
        flash("This trip can't be rated yet.", "error")
        return redirect(url_for("booking.history"))

    stars = request.form.get("stars", type=int, default=5)
    stars = max(1, min(5, stars))
    comment = request.form.get("comment", "").strip() or None

    rating_kwargs = {"ride_booking_id": booking.id} if kind == "ride" else {"delivery_booking_id": booking.id}
    db.session.add(
        Rating(
            **rating_kwargs,
            rater_id=current_user.id,
            ratee_id=booking.driver.user_id,
            stars=stars,
            comment=comment,
        )
    )

    driver_ratings = Rating.query.filter_by(ratee_id=booking.driver.user_id).all()
    all_stars = [r.stars for r in driver_ratings] + [stars]
    booking.driver.rating_avg = round(sum(all_stars) / len(all_stars), 2)

    db.session.commit()
    flash("Thanks for rating your trip!", "success")
    return redirect(url_for("booking.history"))


def _create_ride_booking(form) -> RideBooking:
    vehicle_type = VehicleType.query.filter_by(code=form.vehicle_type.data).first()
    pickup_geo = maps.geocode(form.pickup_address.data)
    dropoff_geo = maps.geocode(form.dropoff_address.data)

    distance_km, duration_minutes = 6.0, 18.0
    if pickup_geo and dropoff_geo:
        route = maps.get_route(pickup_geo["lat"], pickup_geo["lng"], dropoff_geo["lat"], dropoff_geo["lng"])
        if route:
            distance_km, duration_minutes = route["distance_km"], route["duration_minutes"]

    low, high = pricing.estimate_fare(
        distance_km, duration_minutes, vehicle_type.base_fare, vehicle_type.per_km_rate, vehicle_type.per_minute_rate
    )

    booking = RideBooking(
        passenger_id=current_user.id,
        vehicle_type_id=vehicle_type.id if vehicle_type else None,
        pickup_address=form.pickup_address.data,
        pickup_lat=pickup_geo["lat"] if pickup_geo else None,
        pickup_lng=pickup_geo["lng"] if pickup_geo else None,
        dropoff_address=form.dropoff_address.data,
        dropoff_lat=dropoff_geo["lat"] if dropoff_geo else None,
        dropoff_lng=dropoff_geo["lng"] if dropoff_geo else None,
        distance_km=distance_km,
        eta_minutes=round(duration_minutes),
        fare_estimate_low=low,
        fare_estimate_high=high,
    )
    db.session.add(booking)
    db.session.commit()
    notify(current_user.id, "Ride requested", f"Looking for a driver near {form.pickup_address.data}.", icon="car")
    return booking


def _create_delivery_booking(form) -> DeliveryBooking:
    pickup_geo = maps.geocode(form.pickup_address.data)
    dropoff_geo = maps.geocode(form.dropoff_address.data)

    distance_km = 4.0
    if pickup_geo and dropoff_geo:
        route = maps.get_route(pickup_geo["lat"], pickup_geo["lng"], dropoff_geo["lat"], dropoff_geo["lng"])
        distance_km = route["distance_km"] if route else pricing.haversine_km(
            pickup_geo["lat"], pickup_geo["lng"], dropoff_geo["lat"], dropoff_geo["lng"]
        )

    size_rate = {"envelope": 1.0, "parcel": 1.4, "large_box": 2.0}[form.parcel_size.data]
    low = round((300 + distance_km * 100) * size_rate, 2)
    high = round(low * 1.35, 2)

    booking = DeliveryBooking(
        sender_id=current_user.id,
        pickup_address=form.pickup_address.data,
        pickup_lat=pickup_geo["lat"] if pickup_geo else None,
        pickup_lng=pickup_geo["lng"] if pickup_geo else None,
        dropoff_address=form.dropoff_address.data,
        dropoff_lat=dropoff_geo["lat"] if dropoff_geo else None,
        dropoff_lng=dropoff_geo["lng"] if dropoff_geo else None,
        recipient_name=form.recipient_name.data,
        recipient_phone=form.recipient_phone.data,
        parcel_size=ParcelSize(form.parcel_size.data),
        delivery_notes=form.delivery_notes.data,
        distance_km=distance_km,
        fare_estimate_low=low,
        fare_estimate_high=high,
    )
    db.session.add(booking)
    db.session.commit()
    notify(current_user.id, "Delivery requested", f"Looking for a courier near {form.pickup_address.data}.", icon="package")
    return booking
