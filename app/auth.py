"""Authentication: register, login, logout, password reset."""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app import db, limiter
from app.forms import LoginForm, RegistrationForm
from app.models import User

bp = Blueprint("auth", __name__)

RESET_TOKEN_SALT = "password-reset-v1"
RESET_TOKEN_MAX_AGE = 3600  # 1 hour


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=RESET_TOKEN_SALT)


def send_password_reset_email(user: User) -> str:
    token = _serializer().dumps(user.id)
    # Dev mode surfaces the token so the flow works without an SMTP server.
    # Production should replace this with a real email provider integration.
    current_app.logger.info("Password reset link for user %s: %s", user.email, token)
    if not current_app.config.get("TESTING"):
        print(f"[dev-mail] password reset token for {user.email}: {token}")
    return token


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("whispers.dashboard"))
    return render_template(
        "index.html", form=RegistrationForm(), login_form=LoginForm()
    )


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("whispers.dashboard"))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first() is not None:
            form.email.errors.append("This email address is already registered.")
        else:
            user = User(
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip(),
                email=form.email.data.lower(),
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to Whisper! 🤫", "success")
            return redirect(url_for("whispers.dashboard"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("whispers.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Welcome back!", "success")
            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/"):
                next_page = url_for("whispers.dashboard")
            return redirect(next_page)
        # Same message either way — never reveal whether the email exists.
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.index"))


@bp.route("/reset-password", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("whispers.dashboard"))
    token = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user is not None:
            token = send_password_reset_email(user)
        # Always report success: never disclose whether an email is registered.
        flash(
            "If that email is registered, a password reset token has been "
            "generated (shown in the server logs in dev mode).",
            "info",
        )
        if token and current_app.config.get("DEBUG"):
            flash(f"Dev reset token: {token}", "info")
    return render_template("auth/reset_request.html")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_token(token: str):
    if current_user.is_authenticated:
        return redirect(url_for("whispers.dashboard"))
    try:
        user_id = _serializer().loads(token, max_age=RESET_TOKEN_MAX_AGE)
    except (SignatureExpired, BadSignature):
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.reset_request"))
    user = db.session.get(User, int(user_id))
    if user is None:
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.reset_request"))
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        else:
            user.set_password(password)
            db.session.commit()
            flash("Password updated — you can now log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/reset_token.html")
