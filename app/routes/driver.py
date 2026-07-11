from datetime import datetime, date
from decimal import Decimal

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    UserRole, DriverProfile, Vehicle, VehicleType, RideBooking, DeliveryBooking,
    BookingStatus, Rating, TransactionProvider, Trip,
)
from app.utils.decorators import roles_required
from app.services.wallet import credit_wallet
from app.services.notifications import notify

driver_bp = Blueprint("driver", __name__, url_prefix="/driver")


def _profile() -> DriverProfile:
    return current_user.driver_profile


@driver_bp.before_request
@login_required
@roles_required(UserRole.DRIVER)
def _guard():
    pass


@driver_bp.route("/")
def dashboard():
    profile = _profile()
    if not profile.is_approved:
        return render_template("driver/pending_approval.html", status=profile.approval_status)

    today = date.today()
    completed_rides_today = RideBooking.query.filter(
        RideBooking.driver_id == profile.id,
        RideBooking.status == BookingStatus.COMPLETED,
        db.func.date(RideBooking.updated_at) == today,
    ).all()
    completed_deliveries_today = DeliveryBooking.query.filter(
        DeliveryBooking.driver_id == profile.id,
        DeliveryBooking.status == BookingStatus.COMPLETED,
        db.func.date(DeliveryBooking.updated_at) == today,
    ).all()
    today_earnings = sum([float(b.final_fare or 0) for b in completed_rides_today + completed_deliveries_today])

    pending_rides = (
        RideBooking.query.filter_by(status=BookingStatus.PENDING, driver_id=None)
        .order_by(RideBooking.created_at.desc()).limit(10).all()
        if profile.is_online else []
    )
    pending_deliveries = (
        DeliveryBooking.query.filter_by(status=BookingStatus.PENDING, driver_id=None)
        .order_by(DeliveryBooking.created_at.desc()).limit(10).all()
        if profile.is_online else []
    )

    active_ride = RideBooking.query.filter(
        RideBooking.driver_id == profile.id,
        RideBooking.status.in_([BookingStatus.ACCEPTED, BookingStatus.IN_PROGRESS]),
    ).first()
    active_delivery = DeliveryBooking.query.filter(
        DeliveryBooking.driver_id == profile.id,
        DeliveryBooking.status.in_([BookingStatus.ACCEPTED, BookingStatus.IN_PROGRESS]),
    ).first()

    return render_template(
        "driver/dashboard.html",
        profile=profile,
        today_earnings=today_earnings,
        trips_today=len(completed_rides_today) + len(completed_deliveries_today),
        pending_rides=pending_rides,
        pending_deliveries=pending_deliveries,
        active_ride=active_ride,
        active_delivery=active_delivery,
    )


@driver_bp.route("/toggle-online", methods=["POST"])
def toggle_online():
    profile = _profile()
    profile.is_online = not profile.is_online
    db.session.commit()
    flash("You're now online." if profile.is_online else "You're now offline.", "success")
    return redirect(url_for("driver.dashboard"))


@driver_bp.route("/rides/<int:booking_id>/accept", methods=["POST"])
def accept_ride(booking_id):
    profile = _profile()
    booking = RideBooking.query.get_or_404(booking_id)
    if booking.driver_id is not None or booking.status != BookingStatus.PENDING:
        flash("This ride has already been taken.", "error")
        return redirect(url_for("driver.dashboard"))
    booking.driver_id = profile.id
    booking.status = BookingStatus.ACCEPTED
    booking.updated_at = datetime.utcnow()
    db.session.add(Trip(ride_booking_id=booking.id, started_at=datetime.utcnow()))
    db.session.commit()
    notify(booking.passenger_id, "Driver matched", f"{current_user.full_name} accepted your ride request.", icon="car")
    flash("Ride accepted.", "success")
    return redirect(url_for("driver.dashboard"))


@driver_bp.route("/deliveries/<int:booking_id>/accept", methods=["POST"])
def accept_delivery(booking_id):
    profile = _profile()
    booking = DeliveryBooking.query.get_or_404(booking_id)
    if booking.driver_id is not None or booking.status != BookingStatus.PENDING:
        flash("This delivery has already been taken.", "error")
        return redirect(url_for("driver.dashboard"))
    booking.driver_id = profile.id
    booking.status = BookingStatus.ACCEPTED
    booking.updated_at = datetime.utcnow()
    db.session.add(Trip(delivery_booking_id=booking.id, started_at=datetime.utcnow()))
    db.session.commit()
    notify(booking.sender_id, "Courier matched", f"{current_user.full_name} accepted your delivery request.", icon="package")
    flash("Delivery accepted.", "success")
    return redirect(url_for("driver.dashboard"))


@driver_bp.route("/rides/<int:booking_id>/complete", methods=["POST"])
def complete_ride(booking_id):
    profile = _profile()
    booking = RideBooking.query.filter_by(id=booking_id, driver_id=profile.id).first_or_404()
    booking.status = BookingStatus.COMPLETED
    booking.final_fare = booking.final_fare or booking.fare_estimate_low
    booking.updated_at = datetime.utcnow()
    if booking.trip:
        booking.trip.ended_at = datetime.utcnow()
        if booking.trip.started_at:
            booking.trip.actual_duration_minutes = round(
                (booking.trip.ended_at - booking.trip.started_at).total_seconds() / 60
            )
        booking.trip.actual_distance_km = booking.distance_km
    _payout_driver(profile, booking.final_fare)
    profile.total_trips = (profile.total_trips or 0) + 1
    db.session.commit()
    notify(booking.passenger_id, "Trip completed", "Your trip has ended. Rate your driver!", icon="check-circle")
    flash("Ride marked as completed.", "success")
    return redirect(url_for("driver.dashboard"))


@driver_bp.route("/deliveries/<int:booking_id>/complete", methods=["POST"])
def complete_delivery(booking_id):
    profile = _profile()
    booking = DeliveryBooking.query.filter_by(id=booking_id, driver_id=profile.id).first_or_404()
    booking.status = BookingStatus.COMPLETED
    booking.final_fare = booking.final_fare or booking.fare_estimate_low
    booking.updated_at = datetime.utcnow()
    if booking.trip:
        booking.trip.ended_at = datetime.utcnow()
        if booking.trip.started_at:
            booking.trip.actual_duration_minutes = round(
                (booking.trip.ended_at - booking.trip.started_at).total_seconds() / 60
            )
        booking.trip.actual_distance_km = booking.distance_km
    _payout_driver(profile, booking.final_fare)
    profile.total_trips = (profile.total_trips or 0) + 1
    db.session.commit()
    notify(booking.sender_id, "Delivery completed", "Your parcel has been delivered.", icon="check-circle")
    flash("Delivery marked as completed.", "success")
    return redirect(url_for("driver.dashboard"))


def _payout_driver(profile: DriverProfile, fare) -> None:
    fare = Decimal(str(fare or 0))
    commission = fare * Decimal(str(profile.commission_rate or 0.12))
    payout = fare - commission
    wallet = current_user.wallet
    if wallet:
        credit_wallet(wallet, payout, TransactionProvider.WALLET, "Trip payout")


@driver_bp.route("/trips")
def trips():
    profile = _profile()
    rides = RideBooking.query.filter_by(driver_id=profile.id, status=BookingStatus.COMPLETED).order_by(RideBooking.updated_at.desc()).all()
    deliveries = DeliveryBooking.query.filter_by(driver_id=profile.id, status=BookingStatus.COMPLETED).order_by(DeliveryBooking.updated_at.desc()).all()
    combined = sorted(
        [{"kind": "ride", "obj": r} for r in rides] + [{"kind": "delivery", "obj": d} for d in deliveries],
        key=lambda b: b["obj"].updated_at, reverse=True,
    )
    return render_template("driver/trips.html", bookings=combined)


@driver_bp.route("/vehicles", methods=["GET", "POST"])
def vehicles():
    profile = _profile()
    if request.method == "POST":
        vt = VehicleType.query.filter_by(code=request.form.get("vehicle_type", "standard")).first()
        db.session.add(
            Vehicle(
                driver_id=profile.id,
                vehicle_type_id=vt.id if vt else None,
                make=request.form.get("make", "").strip(),
                model=request.form.get("model", "").strip(),
                year=request.form.get("year", type=int),
                color=request.form.get("color", "").strip(),
                plate_number=request.form.get("plate_number", "").strip().upper(),
            )
        )
        db.session.commit()
        flash("Vehicle added.", "success")
        return redirect(url_for("driver.vehicles"))

    vehicle_types = VehicleType.query.filter_by(is_active=True).all()
    return render_template("driver/vehicles.html", vehicles=profile.vehicles.all(), vehicle_types=vehicle_types)


@driver_bp.route("/ratings")
def ratings():
    profile = _profile()
    received = Rating.query.filter_by(ratee_id=current_user.id).order_by(Rating.created_at.desc()).all()
    return render_template("driver/ratings.html", ratings=received, avg=profile.rating_avg)
