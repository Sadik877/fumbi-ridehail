from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    RideBooking, DeliveryBooking, BookingStatus, Notification, Wallet,
    SavedLocation, EmergencyContact, UserRole,
)
from app.services.wallet import credit_wallet, debit_wallet, InsufficientFundsError
from app.models import TransactionProvider

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    if current_user.role == UserRole.DRIVER:
        return redirect(url_for("driver.dashboard"))
    if current_user.role == UserRole.BUSINESS:
        return redirect(url_for("business.dashboard"))
    if current_user.role == UserRole.ADMIN:
        return redirect(url_for("admin.dashboard"))

    wallet = _get_or_create_wallet()

    ride_bookings = RideBooking.query.filter_by(passenger_id=current_user.id)
    delivery_bookings = DeliveryBooking.query.filter_by(sender_id=current_user.id)

    total_trips = ride_bookings.filter_by(status=BookingStatus.COMPLETED).count() + \
        delivery_bookings.filter_by(status=BookingStatus.COMPLETED).count()
    total_spent = sum(
        [b.final_fare or 0 for b in ride_bookings.filter_by(status=BookingStatus.COMPLETED)]
        + [b.final_fare or 0 for b in delivery_bookings.filter_by(status=BookingStatus.COMPLETED)]
    )

    recent = sorted(
        [{"kind": "ride", "obj": r} for r in ride_bookings.order_by(RideBooking.created_at.desc()).limit(6)]
        + [{"kind": "delivery", "obj": d} for d in delivery_bookings.order_by(DeliveryBooking.created_at.desc()).limit(6)],
        key=lambda b: b["obj"].created_at, reverse=True,
    )[:4]

    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(3).all()

    # Last 7 days of trip activity, oldest first
    activity = _weekly_activity_counts()

    return render_template(
        "dashboard/index.html",
        summary={"total_trips": total_trips, "total_spent": total_spent, "co2_saved_kg": total_trips * 0.35},
        wallet=wallet,
        bookings=recent,
        notifications=notifications,
        activity=activity,
        active="overview",
    )


def _weekly_activity_counts():
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    counts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        n = (
            RideBooking.query.filter_by(passenger_id=current_user.id)
            .filter(db.func.date(RideBooking.created_at) == day)
            .count()
            + DeliveryBooking.query.filter_by(sender_id=current_user.id)
            .filter(db.func.date(DeliveryBooking.created_at) == day)
            .count()
        )
        counts.append(n or 0)
    return counts or [0] * 7


def _get_or_create_wallet() -> Wallet:
    wallet = current_user.wallet
    if not wallet:
        wallet = Wallet(user_id=current_user.id)
        db.session.add(wallet)
        db.session.commit()
    return wallet


@dashboard_bp.route("/wallet")
@login_required
def wallet():
    w = _get_or_create_wallet()
    transactions = w.transactions.limit(25).all()
    return render_template("dashboard/wallet.html", wallet=w, transactions=transactions, active="wallet")


@dashboard_bp.route("/wallet/topup", methods=["POST"])
@login_required
def wallet_topup():
    """Wallet top-up via cash/manual credit for now. Card top-ups route
    through Flutterwave/Paystack once real API keys are configured — see
    app/services/payments.py."""
    amount = request.form.get("amount", type=float)
    if not amount or amount <= 0:
        flash("Enter a valid amount.", "error")
        return redirect(url_for("dashboard.wallet"))

    w = _get_or_create_wallet()
    credit_wallet(w, Decimal(str(amount)), TransactionProvider.CASH, "Manual wallet top-up")
    flash(f"₦{amount:,.2f} added to your wallet.", "success")
    return redirect(url_for("dashboard.wallet"))


@dashboard_bp.route("/notifications")
@login_required
def notifications():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return render_template("dashboard/notifications.html", notifications=items, active="notifications")


@dashboard_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", current_user.full_name).strip()
        current_user.city = request.form.get("city", current_user.city)
        phone = request.form.get("phone", current_user.phone).strip()
        email = request.form.get("email", current_user.email).strip().lower()

        from app.models import User
        if User.query.filter(User.email == email, User.id != current_user.id).first():
            flash("That email is already in use by another account.", "error")
            return redirect(url_for("dashboard.profile"))
        if User.query.filter(User.phone == phone, User.id != current_user.id).first():
            flash("That phone number is already in use by another account.", "error")
            return redirect(url_for("dashboard.profile"))

        current_user.email = email
        current_user.phone = phone
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("dashboard.profile"))

    saved_locations = SavedLocation.query.filter_by(user_id=current_user.id).all()
    emergency_contacts = EmergencyContact.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "dashboard/profile.html",
        saved_locations=saved_locations,
        emergency_contacts=emergency_contacts,
        active="profile",
    )


@dashboard_bp.route("/emergency-contacts", methods=["POST"])
@login_required
def add_emergency_contact():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    if not name or not phone:
        flash("Name and phone number are required.", "error")
    else:
        db.session.add(EmergencyContact(user_id=current_user.id, name=name, phone=phone,
                                         relationship_label=request.form.get("relationship", "")))
        db.session.commit()
        flash("Emergency contact added.", "success")
    return redirect(url_for("dashboard.profile"))


@dashboard_bp.route("/saved-locations", methods=["POST"])
@login_required
def add_saved_location():
    label = request.form.get("label", "").strip()
    address = request.form.get("address", "").strip()
    if not label or not address:
        flash("Label and address are required.", "error")
    else:
        db.session.add(SavedLocation(user_id=current_user.id, label=label, address=address))
        db.session.commit()
        flash("Location saved.", "success")
    return redirect(url_for("dashboard.profile"))
