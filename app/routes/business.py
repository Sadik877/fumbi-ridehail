from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import UserRole, DeliveryBooking, BookingStatus, ParcelSize
from app.utils.decorators import roles_required
from app.services import maps, pricing
from app.services.notifications import notify

business_bp = Blueprint("business", __name__, url_prefix="/business")


@business_bp.before_request
@login_required
@roles_required(UserRole.BUSINESS)
def _guard():
    pass


@business_bp.route("/")
def dashboard():
    profile = current_user.business_profile
    deliveries = DeliveryBooking.query.filter_by(sender_id=current_user.id).order_by(DeliveryBooking.created_at.desc())
    total = deliveries.count()
    completed = deliveries.filter_by(status=BookingStatus.COMPLETED).count()
    total_spend = sum(float(d.final_fare or 0) for d in deliveries.filter_by(status=BookingStatus.COMPLETED))

    return render_template(
        "business/dashboard.html",
        profile=profile,
        deliveries=deliveries.limit(8).all(),
        total_deliveries=total,
        completed_deliveries=completed,
        total_spend=total_spend,
    )


@business_bp.route("/bulk-delivery", methods=["GET", "POST"])
def bulk_delivery():
    if request.method == "POST":
        pickup = request.form.get("pickup_address", "").strip()
        rows = zip(
            request.form.getlist("dropoff_address[]"),
            request.form.getlist("recipient_name[]"),
            request.form.getlist("recipient_phone[]"),
            request.form.getlist("parcel_size[]"),
        )
        created = 0
        for dropoff, name, phone, size in rows:
            if not (dropoff and name and phone):
                continue
            pickup_geo = maps.geocode(pickup)
            dropoff_geo = maps.geocode(dropoff)
            distance_km = 4.0
            if pickup_geo and dropoff_geo:
                distance_km = pricing.haversine_km(
                    pickup_geo["lat"], pickup_geo["lng"], dropoff_geo["lat"], dropoff_geo["lng"]
                )
            low = round(300 + distance_km * 100, 2)
            db.session.add(
                DeliveryBooking(
                    sender_id=current_user.id,
                    pickup_address=pickup,
                    pickup_lat=pickup_geo["lat"] if pickup_geo else None,
                    pickup_lng=pickup_geo["lng"] if pickup_geo else None,
                    dropoff_address=dropoff,
                    dropoff_lat=dropoff_geo["lat"] if dropoff_geo else None,
                    dropoff_lng=dropoff_geo["lng"] if dropoff_geo else None,
                    recipient_name=name,
                    recipient_phone=phone,
                    parcel_size=ParcelSize(size) if size in ParcelSize._value2member_map_ else ParcelSize.PARCEL,
                    distance_km=distance_km,
                    fare_estimate_low=low,
                    fare_estimate_high=round(low * 1.35, 2),
                )
            )
            created += 1
        db.session.commit()
        flash(f"{created} deliveries created.", "success")
        return redirect(url_for("business.dashboard"))

    return render_template("business/bulk_delivery.html")


@business_bp.route("/deliveries")
def deliveries():
    status = request.args.get("status", "all")
    query = DeliveryBooking.query.filter_by(sender_id=current_user.id)
    if status != "all":
        query = query.filter_by(status=BookingStatus(status))
    items = query.order_by(DeliveryBooking.created_at.desc()).all()
    return render_template("business/deliveries.html", deliveries=items, active_status=status)


@business_bp.route("/invoices")
def invoices():
    completed = (
        DeliveryBooking.query.filter_by(sender_id=current_user.id, status=BookingStatus.COMPLETED)
        .order_by(DeliveryBooking.updated_at.desc()).all()
    )
    total = sum(float(d.final_fare or 0) for d in completed)
    return render_template("business/invoices.html", deliveries=completed, total=total)


@business_bp.route("/reports")
def reports():
    deliveries = DeliveryBooking.query.filter_by(sender_id=current_user.id).all()
    by_month = {}
    for d in deliveries:
        key = d.created_at.strftime("%b %Y")
        by_month.setdefault(key, {"count": 0, "spend": 0.0})
        by_month[key]["count"] += 1
        if d.status == BookingStatus.COMPLETED:
            by_month[key]["spend"] += float(d.final_fare or 0)
    return render_template("business/reports.html", by_month=by_month)
