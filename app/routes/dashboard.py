from flask import Blueprint, render_template

from app import mock_data as data

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
def index():
    return render_template(
        "dashboard/index.html",
        user=data.CURRENT_USER,
        summary=data.DASHBOARD_SUMMARY,
        wallet=data.WALLET,
        bookings=data.BOOKINGS[:4],
        notifications=data.NOTIFICATIONS[:3],
        activity=data.RECENT_ACTIVITY_CHART,
        active="overview",
    )


@dashboard_bp.route("/wallet")
def wallet():
    return render_template(
        "dashboard/wallet.html",
        wallet=data.WALLET,
        transactions=data.WALLET_TRANSACTIONS,
        active="wallet",
    )


@dashboard_bp.route("/notifications")
def notifications():
    return render_template(
        "dashboard/notifications.html", notifications=data.NOTIFICATIONS, active="notifications"
    )


@dashboard_bp.route("/profile")
def profile():
    return render_template("dashboard/profile.html", user=data.CURRENT_USER, active="profile")
