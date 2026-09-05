"""Shared pytest fixtures: in-memory app, database, and logged-in clients."""

import pytest

from app import create_app
from app import db as _db
from app.models import Follow, User, Whisper


@pytest.fixture()
def app(tmp_path):
    app = create_app("testing")
    app.config["UPLOAD_FOLDER"] = tmp_path / "uploads"
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db(app):
    return app.extensions["sqlalchemy"]


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def user(db):
    u = User(first_name="Jane", last_name="Doe", email="jane@example.com")
    u.set_password("sup3rs3cret!")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture()
def other_user(db):
    u = User(first_name="John", last_name="Smith", email="john@example.com")
    u.set_password("sup3rs3cret!")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture()
def logged_in_client(client, user):
    client.post("/login", data={"email": user.email, "password": "sup3rs3cret!"})
    return client


def make_whisper(db, author, body="hello secret world"):
    from app.crypto import encrypt_message

    w = Whisper(body=encrypt_message(body, author.id), author_id=author.id)
    db.session.add(w)
    db.session.commit()
    return w


def follow(db, follower, followed):
    db.session.add(Follow(follower_id=follower.id, followed_id=followed.id))
    db.session.commit()
