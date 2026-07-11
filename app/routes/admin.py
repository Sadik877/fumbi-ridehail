from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    UserRole, User, DriverProfile, RideBooking, DeliveryBooking, BookingStatus,
    Transaction, SupportTicket, TicketStatus, PromoCode, DiscountType,
)
from app.utils.decorators import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
@roles_required(UserRole.ADMIN)
def _guard():
    pass


@admin_bp.route("/")
def dashboard():
    since = datetime.utcnow() - timedelta(days=30)
    stats = {
        "total_users": User.query.count(),
        "total_drivers": DriverProfile.query.count(),
        "pending_driver_approvals": DriverProfile.query.filter_by(is_approved=False).count(),
        "total_rides": RideBooking.query.count(),
        "total_deliveries": DeliveryBooking.query.count(),
        "rides_last_30d": RideBooking.query.filter(RideBooking.created_at >= since).count(),
        "open_tickets": SupportTicket.query.filter(SupportTicket.status != TicketStatus.CLOSED).count(),
        "gross_transaction_volume": db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).scalar(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(6).all()
    pending_drivers = DriverProfile.query.filter_by(is_approved=False).limit(6).all()
    return render_template("admin/dashboard.html", stats=stats, recent_users=recent_users, pending_drivers=pending_drivers)


@admin_bp.route("/users")
def users():
    role_filter = request.args.get("role", "all")
    q = request.args.get("q", "").strip()
    query = User.query
    if role_filter != "all":
        query = query.filter_by(role=UserRole(role_filter))
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(User.full_name.ilike(like), User.email.ilike(like), User.phone.ilike(like)))
    items = query.order_by(User.created_at.desc()).limit(100).all()
    return render_template("admin/users.html", users=items, role_filter=role_filter, q=q)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't deactivate your own account.", "error")
        return redirect(url_for("admin.users"))
    user.is_active_account = not user.is_active_account
    db.session.commit()
    flash(f"{user.full_name} is now {'active' if user.is_active_account else 'suspended'}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/drivers")
def drivers():
    status = request.args.get("status", "pending")
    query = DriverProfile.query
    if status == "pending":
        query = query.filter_by(is_approved=False)
    elif status == "approved":
        query = query.filter_by(is_approved=True)
    items = query.order_by(DriverProfile.created_at.desc()).all()
    return render_template("admin/drivers.html", drivers=items, status=status)


@admin_bp.route("/drivers/<int:profile_id>/approve", methods=["POST"])
def approve_driver(profile_id):
    profile = DriverProfile.query.get_or_404(profile_id)
    profile.is_approved = True
    profile.approval_status = "approved"
    db.session.commit()
    flash(f"{profile.user.full_name} approved as a driver.", "success")
    return redirect(url_for("admin.drivers"))


@admin_bp.route("/drivers/<int:profile_id>/reject", methods=["POST"])
def reject_driver(profile_id):
    profile = DriverProfile.query.get_or_404(profile_id)
    profile.is_approved = False
    profile.approval_status = "rejected"
    db.session.commit()
    flash(f"{profile.user.full_name}'s driver application was rejected.", "success")
    return redirect(url_for("admin.drivers"))


@admin_bp.route("/bookings")
def bookings():
    status = request.args.get("status", "all")
    ride_q = RideBooking.query
    delivery_q = DeliveryBooking.query
    if status != "all":
        ride_q = ride_q.filter_by(status=BookingStatus(status))
        delivery_q = delivery_q.filter_by(status=BookingStatus(status))
    combined = sorted(
        [{"kind": "ride", "obj": r} for r in ride_q.order_by(RideBooking.created_at.desc()).limit(50)]
        + [{"kind": "delivery", "obj": d} for d in delivery_q.order_by(DeliveryBooking.created_at.desc()).limit(50)],
        key=lambda b: b["obj"].created_at, reverse=True,
    )[:60]
    return render_template("admin/bookings.html", bookings=combined, status=status)


@admin_bp.route("/payments")
def payments():
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(100).all()
    return render_template("admin/payments.html", transactions=transactions)


@admin_bp.route("/support")
def support():
    status = request.args.get("status", "open")
    query = SupportTicket.query
    if status != "all":
        query = query.filter_by(status=TicketStatus(status))
    tickets = query.order_by(SupportTicket.created_at.desc()).all()
    return render_template("admin/support.html", tickets=tickets, status=status)


@admin_bp.route("/support/<int:ticket_id>/resolve", methods=["POST"])
def resolve_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    ticket.status = TicketStatus.RESOLVED
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Ticket marked resolved.", "success")
    return redirect(url_for("admin.support"))


@admin_bp.route("/coupons", methods=["GET", "POST"])
def coupons():
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        if PromoCode.query.filter_by(code=code).first():
            flash("That coupon code already exists.", "error")
        else:
            db.session.add(
                PromoCode(
                    code=code,
                    description=request.form.get("description", ""),
                    discount_type=DiscountType(request.form.get("discount_type", "percentage")),
                    discount_value=request.form.get("discount_value", type=float, default=0),
                    max_uses=request.form.get("max_uses", type=int),
                )
            )
            db.session.commit()
            flash("Coupon created.", "success")
        return redirect(url_for("admin.coupons"))

    items = PromoCode.query.order_by(PromoCode.valid_from.desc()).all()
    return render_template("admin/coupons.html", coupons=items)


@admin_bp.route("/coupons/<int:coupon_id>/toggle", methods=["POST"])
def toggle_coupon(coupon_id):
    coupon = PromoCode.query.get_or_404(coupon_id)
    coupon.is_active = not coupon.is_active
    db.session.commit()
    return redirect(url_for("admin.coupons"))
