from flask import Blueprint, jsonify, render_template, request

from app import mock_data as data

booking_bp = Blueprint("booking", __name__, url_prefix="/book")


@booking_bp.route("/ride")
def ride():
    return render_template("booking/ride.html")


@booking_bp.route("/delivery")
def delivery():
    return render_template("booking/delivery.html")


@booking_bp.route("/history")
def history():
    status = request.args.get("status", "all")
    bookings = data.BOOKINGS
    if status != "all":
        bookings = [b for b in bookings if b["status"] == status]
    return render_template(
        "booking/history.html", bookings=bookings, active_status=status, active="history"
    )


@booking_bp.route("/estimate", methods=["POST"])
def estimate():
    """Mock fare estimate endpoint used by the booking widgets' JS.
    Swap this for a real pricing engine call keyed on distance/ETA."""
    payload = request.get_json(silent=True) or {}
    tier = payload.get("tier", "standard")
    base = {"standard": 4.5, "comfort": 7.0, "xl": 9.5}.get(tier, 4.5)
    return jsonify(
        {
            "fare_low": round(base, 2),
            "fare_high": round(base * 1.35, 2),
            "eta_minutes": 4,
            "currency": "USD",
        }
    )
