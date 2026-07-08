from flask import Blueprint, render_template, request

from app import mock_data as data

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def landing():
    return render_template(
        "landing.html",
        stats=data.STATS,
        features=data.FEATURES,
        why_us=data.WHY_US,
        testimonials=data.TESTIMONIALS,
        faqs=data.FAQS[:4],
    )


@main_bp.route("/about")
def about():
    return render_template("about.html", stats=data.STATS)


@main_bp.route("/contact")
def contact():
    return render_template("contact.html")


@main_bp.route("/contact/submit", methods=["POST"])
def contact_submit():
    # Placeholder — wire up to a ticketing system / email service later.
    name = request.form.get("name", "")
    return render_template("contact.html", submitted=True, name=name)


@main_bp.route("/faq")
def faq():
    return render_template("faq.html", faqs=data.FAQS)
