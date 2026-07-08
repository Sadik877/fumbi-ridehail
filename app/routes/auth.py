from flask import Blueprint, redirect, render_template, request, url_for

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Placeholder — verify credentials against the user store here.
        return redirect(url_for("dashboard.index"))
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Placeholder — create the account, send verification, etc.
        return redirect(url_for("dashboard.index"))
    return render_template("auth/register.html")


@auth_bp.route("/register/driver", methods=["GET", "POST"])
def driver_register():
    if request.method == "POST":
        # Placeholder — persist applicant + uploaded documents for review.
        return render_template("auth/driver_register.html", submitted=True)
    return render_template("auth/driver_register.html")


@auth_bp.route("/logout")
def logout():
    # Placeholder — clear session.
    return redirect(url_for("main.landing"))
