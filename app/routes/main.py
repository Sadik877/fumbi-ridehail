from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user
from sqlalchemy import func

from app import content
from app.extensions import db, limiter
from app.forms import ContactForm
from app.models import DriverProfile, RideBooking, DeliveryBooking, Review, BookingStatus, User, UserRole, SupportTicket

main_bp = Blueprint("main", __name__)


def _live_stats():
    completed_rides = RideBooking.query.filter_by(status=BookingStatus.COMPLETED).count()
    completed_deliveries = DeliveryBooking.query.filter_by(status=BookingStatus.COMPLETED).count()
    active_drivers = DriverProfile.query.filter_by(is_approved=True).count()
    avg_rating = db.session.query(func.avg(DriverProfile.rating_avg)).scalar() or 4.8

    total_users = User.query.count()
    return [
        {"value": f"{completed_rides + completed_deliveries:,}+", "label": "Trips completed"},
        {"value": f"{total_users:,}", "label": "Registered users"},
        {"value": f"{active_drivers:,}", "label": "Verified drivers"},
        {"value": f"{avg_rating:.1f}/5", "label": "Average rating"},
    ]


@main_bp.route("/")
def landing():
    reviews = Review.query.filter_by(is_published=True).order_by(Review.created_at.desc()).limit(3).all()
    return render_template(
        "landing.html",
        stats=_live_stats(),
        features=content.FEATURES,
        why_us=content.WHY_US,
        testimonials=reviews,
        faqs=content.FAQS[:4],
    )


@main_bp.route("/about")
def about():
    return render_template("about.html", stats=_live_stats())


@main_bp.route("/contact", methods=["GET"])
def contact():
    form = ContactForm()
    return render_template("contact.html", form=form)


@main_bp.route("/contact/submit", methods=["POST"])
@limiter.limit("5 per minute")
def contact_submit():
    form = ContactForm()
    if not form.validate_on_submit():
        return render_template("contact.html", form=form), 400

    if current_user.is_authenticated:
        ticket = SupportTicket(
            user_id=current_user.id,
            subject=f"[{form.topic.data}] Contact form",
            message=form.message.data,
            topic=form.topic.data,
        )
        db.session.add(ticket)
        db.session.commit()

    flash("Thanks — your message has been sent. Our team typically replies within a few hours.", "success")
    return render_template("contact.html", form=ContactForm(formdata=None), submitted=True, name=form.name.data)


@main_bp.route("/faq")
def faq():
    return render_template("faq.html", faqs=content.FAQS)


@main_bp.route("/privacy")
def privacy():
    return render_template("legal/privacy.html")


@main_bp.route("/terms")
def terms():
    return render_template("legal/terms.html")


@main_bp.route("/cookies")
def cookies():
    return render_template("legal/cookies.html")
