from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SelectField, TextAreaField, DecimalField
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, Regexp


PHONE_REGEX = r"^\+?[0-9\s\-]{7,20}$"


class LoginForm(FlaskForm):
    identifier = StringField("Email or phone", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")


class RegisterForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone number", validators=[DataRequired(), Regexp(PHONE_REGEX, message="Enter a valid phone number")])
    city = StringField("City", validators=[Optional(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, message="Use at least 8 characters")])
    confirm_password = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )


class DriverRegisterForm(RegisterForm):
    license_number = StringField("Driver's license number", validators=[DataRequired(), Length(max=64)])
    vehicle_make = StringField("Vehicle make & model", validators=[DataRequired(), Length(max=120)])
    vehicle_year = StringField("Year", validators=[Optional(), Length(max=4)])
    plate_number = StringField("License plate", validators=[DataRequired(), Length(max=20)])
    vehicle_type = SelectField(
        "Vehicle type", choices=[("standard", "Standard"), ("comfort", "Comfort"), ("xl", "XL")]
    )


class BusinessRegisterForm(RegisterForm):
    company_name = StringField("Company name", validators=[DataRequired(), Length(max=150)])
    registration_number = StringField("Registration number", validators=[Optional(), Length(max=80)])
    industry = StringField("Industry", validators=[Optional(), Length(max=80)])


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm new password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    topic = SelectField(
        "Topic",
        choices=[
            ("A recent trip", "A recent trip"),
            ("A recent delivery", "A recent delivery"),
            ("Billing", "Billing"),
            ("Partnerships", "Partnerships"),
            ("Something else", "Something else"),
        ],
    )
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=2000)])


class RideBookingForm(FlaskForm):
    pickup_address = StringField("Pickup", validators=[DataRequired(), Length(max=255)])
    dropoff_address = StringField("Drop-off", validators=[DataRequired(), Length(max=255)])
    vehicle_type = SelectField("Vehicle type", choices=[("standard", "Standard"), ("comfort", "Comfort"), ("xl", "XL")])
    scheduled_at = StringField("Scheduled time", validators=[Optional()])


class DeliveryBookingForm(FlaskForm):
    pickup_address = StringField("Pickup", validators=[DataRequired(), Length(max=255)])
    dropoff_address = StringField("Drop-off", validators=[DataRequired(), Length(max=255)])
    recipient_name = StringField("Recipient name", validators=[DataRequired(), Length(max=120)])
    recipient_phone = StringField("Recipient phone", validators=[DataRequired(), Regexp(PHONE_REGEX)])
    parcel_size = SelectField(
        "Parcel size", choices=[("envelope", "Envelope"), ("parcel", "Parcel"), ("large_box", "Large box")]
    )
    delivery_notes = TextAreaField("Notes", validators=[Optional(), Length(max=255)])
