"""Shared WTForms definitions."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    PasswordField,
    StringField,
    TextAreaField,
    ValidationError,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

from app.models import User

NAME_PATTERN = r"^[A-Za-z\u00C0-\u017F' -]+$"


class RegistrationForm(FlaskForm):
    first_name = StringField(
        "First name",
        validators=[DataRequired(), Length(min=2, max=45), Regexp(NAME_PATTERN)],
    )
    last_name = StringField(
        "Last name",
        validators=[DataRequired(), Length(min=2, max=45), Regexp(NAME_PATTERN)],
    )
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128, message="Password must be 8-128 characters."),
        ],
    )
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")


class WhisperForm(FlaskForm):
    body = TextAreaField(
        "Whisper",
        validators=[
            DataRequired(),
            Length(min=5, max=280, message="Whispers are 5-280 characters."),
        ],
    )


class BioForm(FlaskForm):
    bio = TextAreaField("Bio", validators=[DataRequired(), Length(max=500)])


def email_not_registered(_form, field):
    if User.query.filter_by(email=field.data.lower()).first() is not None:
        raise ValidationError("This email address is already registered.")
