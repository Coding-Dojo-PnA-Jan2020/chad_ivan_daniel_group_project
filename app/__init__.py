"""Whisper application factory."""

import os

from flask import Flask, current_app, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)


def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__)

    from dotenv import load_dotenv

    load_dotenv()  # reads .env if present; real env vars still win

    config_name = config_object or os.environ.get("FLASK_CONFIG", "default")
    from app.config import config

    app.config.from_object(config[config_name])
    app.config.from_prefixed_env()
    config[config_name].init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    from app.auth import bp as auth_bp
    from app.users import bp as users_bp
    from app.whispers import bp as whispers_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(whispers_bp)
    app.register_blueprint(users_bp)

    register_error_handlers(app)
    register_template_globals(app)

    return app


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404


def register_template_globals(app: Flask) -> None:
    app.template_filter("avatar")(avatar_url)


def avatar_url(user):
    """Uploaded avatar if present, otherwise a generated DiceBear URL —
    avatars are optional, which keeps the upload attack surface small."""
    if user is not None and user.avatar:
        return f"/uploads/{user.avatar}"
    style = current_app.config["AVATAR_STYLE"]
    seed = f"whisper-{user.id}" if user is not None else "guest"
    return f"https://api.dicebear.com/9.x/{style}/svg?seed={seed}"


from app import models  # noqa: E402,F401  (register models with SQLAlchemy)
