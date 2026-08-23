from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional


class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, message="Use at least 8 characters.")])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class ScanUploadForm(FlaskForm):
    """Patient intake + MRI scan upload, submitted together as one action."""

    patient_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=150)])
    patient_age = IntegerField("Age", validators=[DataRequired(), NumberRange(min=0, max=120)])
    patient_gender = SelectField(
        "Gender",
        choices=[("", "Select gender"), ("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
        validators=[DataRequired()],
    )
    patient_phone = StringField("Phone Number", validators=[Optional(), Length(max=30)])
    patient_address = StringField("Address", validators=[Optional(), Length(max=255)])
    scan_image = FileField(
        "MRI Scan",
        validators=[
            FileRequired(message="Please choose an MRI image to upload."),
            FileAllowed(["png", "jpg", "jpeg"], "Only PNG and JPG images are supported."),
        ],
    )
    submit = SubmitField("Analyze Scan")


class DeleteForm(FlaskForm):
    """CSRF-only form backing the per-row delete button on the results table."""


class ProfileForm(FlaskForm):
    """Account settings: name, email, and an optional password change — all
    gated behind confirming the current password."""

    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired(message="Enter your current password to save changes.")],
    )
    new_password = PasswordField(
        "New Password", validators=[Optional(), Length(min=8, message="Use at least 8 characters.")]
    )
    confirm_new_password = PasswordField(
        "Confirm New Password", validators=[EqualTo("new_password", message="New passwords must match.")]
    )
    submit = SubmitField("Save Changes")
