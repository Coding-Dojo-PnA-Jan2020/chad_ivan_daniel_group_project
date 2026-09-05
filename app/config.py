"""Application configuration. All secrets come from the environment —
nothing sensitive is ever committed to the repository."""

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    # Dev fallback generates a random per-process key; ProductionConfig
    # refuses to start without SECRET_KEY set in the environment.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + str(BASE_DIR / "whisper_local.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # hard 2 MB request cap
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
    AVATAR_STYLE = os.environ.get("AVATAR_STYLE", "adventurer")

    # Session hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 hours

    WTF_CSRF_TIME_LIMIT = None

    @classmethod
    def init_app(cls, app) -> None:
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SECRET_KEY = "test-secret-key-not-for-production"
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = BASE_DIR / "tests" / "tmp_uploads"


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    @classmethod
    def init_app(cls, app):
        super().init_app(app)
        if not os.environ.get("SECRET_KEY"):
            raise RuntimeError(
                "SECRET_KEY must be set in the environment when running in production."
            )


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
