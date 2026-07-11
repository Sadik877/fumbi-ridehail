from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, limiter
from app.forms import (
    LoginForm, RegisterForm, DriverRegisterForm, BusinessRegisterForm,
    ForgotPasswordForm, ResetPasswordForm,
)
from app.models import (
    User, UserRole, PassengerProfile, DriverProfile, Vehicle, VehicleType,
    BusinessProfile, Wallet,
)
from app.services.email import send_email

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _redirect_for_role(user: User):
    return {
        UserRole.DRIVER: "driver.dashboard",
        UserRole.BUSINESS: "business.dashboard",
        UserRole.ADMIN: "admin.dashboard",
    }.get(user.role, "dashboard.index")


def _email_or_phone_taken(email, phone):
    return User.query.filter((User.email == email) | (User.phone == phone)).first()


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for(_redirect_for_role(current_user)))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data.strip().lower()
        user = User.query.filter(
            (User.email == identifier) | (User.phone == form.identifier.data.strip())
        ).first()

        if user and user.check_password(form.password.data):
            if not user.is_active_account:
                flash("Your account has been suspended. Contact support for help.", "error")
                return render_template("auth/login.html", form=form)
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=form.remember.data)
            return redirect(request.args.get("next") or url_for(_redirect_for_role(user)))

        flash("Incorrect email/phone or password.", "error")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for(_redirect_for_role(current_user)))

    form = RegisterForm()
    if form.validate_on_submit():
        if _email_or_phone_taken(form.email.data.lower(), form.phone.data.strip()):
            flash("An account with that email or phone number already exists.", "error")
            return render_template("auth/register.html", form=form)

        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip(),
            city=form.city.data.strip() if form.city.data else None,
            role=UserRole.PASSENGER,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        db.session.add(PassengerProfile(user_id=user.id))
        db.session.add(Wallet(user_id=user.id))
        db.session.commit()

        _send_verification_email(user)
        login_user(user)
        flash("Welcome to MoveX! Check your email to verify your account.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/register/driver", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def driver_register():
    form = DriverRegisterForm()
    if form.validate_on_submit():
        if _email_or_phone_taken(form.email.data.lower(), form.phone.data.strip()):
            flash("An account with that email or phone number already exists.", "error")
            return render_template("auth/driver_register.html", form=form)
        if Vehicle.query.filter_by(plate_number=form.plate_number.data.strip().upper()).first():
            flash("That license plate is already registered.", "error")
            return render_template("auth/driver_register.html", form=form)

        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip(),
            city=form.city.data.strip() if form.city.data else None,
            role=UserRole.DRIVER,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        driver_profile = DriverProfile(
            user_id=user.id,
            license_number=form.license_number.data.strip(),
            approval_status="pending",
        )
        db.session.add(driver_profile)
        db.session.flush()

        vehicle_type = VehicleType.query.filter_by(code=form.vehicle_type.data).first()
        year = int(form.vehicle_year.data) if form.vehicle_year.data and form.vehicle_year.data.isdigit() else None
        db.session.add(
            Vehicle(
                driver_id=driver_profile.id,
                vehicle_type_id=vehicle_type.id if vehicle_type else None,
                make=form.vehicle_make.data.strip(),
                model="",
                year=year,
                plate_number=form.plate_number.data.strip().upper(),
            )
        )
        db.session.add(Wallet(user_id=user.id))
        db.session.commit()

        _send_verification_email(user)
        return render_template("auth/driver_register.html", form=DriverRegisterForm(formdata=None), submitted=True)

    return render_template("auth/driver_register.html", form=form)


@auth_bp.route("/register/business", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def business_register():
    form = BusinessRegisterForm()
    if form.validate_on_submit():
        if _email_or_phone_taken(form.email.data.lower(), form.phone.data.strip()):
            flash("An account with that email or phone number already exists.", "error")
            return render_template("auth/business_register.html", form=form)

        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip(),
            city=form.city.data.strip() if form.city.data else None,
            role=UserRole.BUSINESS,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        db.session.add(
            BusinessProfile(
                user_id=user.id,
                company_name=form.company_name.data.strip(),
                registration_number=form.registration_number.data,
                industry=form.industry.data,
            )
        )
        db.session.add(Wallet(user_id=user.id))
        db.session.commit()

        _send_verification_email(user)
        login_user(user)
        flash("Business account created — verification is typically completed within one business day.", "success")
        return redirect(url_for("business.dashboard"))

    return render_template("auth/business_register.html", form=form)


@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    user = User.verify_token(token, purpose="verify_email", max_age_seconds=86400)
    if not user:
        flash("That verification link is invalid or has expired.", "error")
        return redirect(url_for("main.landing"))
    user.is_email_verified = True
    db.session.commit()
    flash("Email verified — thanks!", "success")
    return redirect(url_for(_redirect_for_role(user)) if current_user.is_authenticated else url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            token = user.get_reset_token()
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_email(
                to=user.email,
                subject="Reset your MoveX password",
                body=f"Reset your password using this link (valid for 1 hour): {reset_url}",
            )
        # Same message whether or not the email exists, so the form can't be
        # used to enumerate registered accounts.
        flash("If that email is registered, a reset link is on its way.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.verify_token(token, purpose="reset", max_age_seconds=3600)
    if not user:
        flash("That reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Password updated — you can log in now.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", form=form, token=token)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.landing"))


def _send_verification_email(user: User):
    token = user.get_email_verification_token()
    verify_url = url_for("auth.verify_email", token=token, _external=True)
    send_email(
        to=user.email,
        subject="Verify your MoveX email",
        body=f"Welcome to MoveX! Verify your email: {verify_url}",
    )
