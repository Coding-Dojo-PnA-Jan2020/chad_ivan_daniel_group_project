"""Security-critical behavior: crypto, auth, permissions, CSRF."""


class TestCrypto:
    def test_roundtrip(self, app):
        from app.crypto import decrypt_message, encrypt_message

        token = encrypt_message("secret message", 42)
        assert decrypt_message(token, 42) == "secret message"

    def test_ciphertext_differs_per_user(self, app):
        from app.crypto import encrypt_message

        assert encrypt_message("same text", 1) != encrypt_message("same text", 2)

    def test_wrong_key_returns_none(self, app):
        from app.crypto import decrypt_message, encrypt_message

        token = encrypt_message("secret message", 1)
        assert decrypt_message(token, 2) is None

    def test_garbage_returns_none(self, app):
        from app.crypto import decrypt_message

        assert decrypt_message("not-a-fernet-token", 1) is None


class TestAuth:
    def test_register_login_logout(self, client, db):
        resp = client.post(
            "/register",
            data={
                "first_name": "Alice",
                "last_name": "Chan",
                "email": "alice@example.com",
                "password": "password123",
                "confirm": "password123",
            },
            follow_redirects=True,
        )
        assert b"Dashboard" in resp.data or resp.status_code == 200
        # logged in now — dashboard works
        assert client.get("/dashboard").status_code == 200
        client.post("/logout")
        assert client.get("/dashboard").status_code == 302

    def test_duplicate_email_rejected(self, client, user):
        resp = client.post(
            "/register",
            data={
                "first_name": "Fake",
                "last_name": "User",
                "email": user.email,
                "password": "password123",
                "confirm": "password123",
            },
        )
        assert b"already registered" in resp.data

    def test_short_password_rejected(self, client):
        resp = client.post(
            "/register",
            data={
                "first_name": "Bob",
                "last_name": "Short",
                "email": "bob@example.com",
                "password": "short",
                "confirm": "short",
            },
        )
        assert b"8-128 characters" in resp.data

    def test_login_wrong_password(self, client, user):
        resp = client.post(
            "/login",
            data={"email": user.email, "password": "wrong-password"},
            follow_redirects=True,
        )
        assert b"Invalid email or password" in resp.data

    def test_login_unknown_user_same_message(self, client):
        resp = client.post(
            "/login",
            data={"email": "ghost@example.com", "password": "whatever123"},
            follow_redirects=True,
        )
        assert b"Invalid email or password" in resp.data

    def test_password_hash_not_plaintext(self, db, user):
        assert user.password_hash != "sup3rs3cret!"
        assert user.password_hash.startswith(("pbkdf2:", "scrypt:", "argon2:"))

    def test_password_reset_flow(self, client, user, db):
        client.post("/reset-password", data={"email": user.email})
        assert client.get("/dashboard").status_code == 302  # still logged out

        from app.auth import _serializer

        token = _serializer().dumps(user.id)
        resp = client.post(
            f"/reset-password/{token}",
            data={"password": "new-password-9", "confirm": "new-password-9"},
            follow_redirects=True,
        )
        assert b"Password updated" in resp.data
        assert user.check_password("new-password-9")

    def test_reset_token_expired_or_invalid(self, client, user):
        resp = client.get("/reset-password/garbage-token", follow_redirects=True)
        assert b"invalid or has expired" in resp.data


class TestAccessControl:
    PROTECTED_GETS = ["/dashboard", "/ninjas", "/users/1"]

    def test_pages_require_login(self, client):
        for url in self.PROTECTED_GETS:
            resp = client.get(url)
            assert resp.status_code == 302, url
            assert "/login" in resp.headers["Location"], url

    def test_state_changes_require_login(self, client, user, other_user, db):
        from tests.conftest import make_whisper

        w = make_whisper(db, user)
        for method, url in [
            ("post", f"/whispers/{w.id}/delete"),
            ("post", f"/whispers/{w.id}/like"),
            ("post", f"/users/{other_user.id}/follow"),
            ("post", "/account/bio"),
        ]:
            resp = getattr(client, method)(url)
            assert resp.status_code == 302, url
            assert "/login" in resp.headers["Location"], url


class TestAuthorization:
    def test_cannot_delete_others_whisper(self, logged_in_client, db, other_user):
        from tests.conftest import make_whisper

        w = make_whisper(db, other_user)
        resp = logged_in_client.post(f"/whispers/{w.id}/delete")
        assert resp.status_code == 403
        # whisper still exists
        assert db.session.get(type(w), w.id) is not None

    def test_cannot_follow_yourself(self, logged_in_client, user):
        assert logged_in_client.post(f"/users/{user.id}/follow").status_code == 403

    def test_feed_shows_only_self_and_followed(
        self, logged_in_client, db, user, other_user
    ):
        from tests.conftest import follow, make_whisper

        make_whisper(db, user, "my own whisper here")
        make_whisper(db, other_user, "a strangers secret whisper")
        resp = logged_in_client.get("/dashboard")
        assert b"my own whisper here" in resp.data
        assert b"a strangers secret whisper" not in resp.data

        follow(db, user, other_user)
        resp = logged_in_client.get("/dashboard")
        assert b"a strangers secret whisper" in resp.data


class TestCsrf:
    def test_csrf_enforced_when_enabled(self, app, user):
        app.config["WTF_CSRF_ENABLED"] = True
        client = app.test_client()
        client.post("/login", data={"email": user.email, "password": "sup3rs3cret!"})
        resp = client.post("/whispers", data={"body": "no token whisper here"})
        assert resp.status_code == 400


class TestModelSecurity:
    def test_like_unique_constraint(self, db, user, other_user):
        import pytest as _pytest
        from sqlalchemy.exc import IntegrityError

        from app.models import Like
        from tests.conftest import make_whisper

        w = make_whisper(db, user)
        db.session.add(Like(user_id=other_user.id, whisper_id=w.id))
        db.session.commit()
        db.session.add(Like(user_id=other_user.id, whisper_id=w.id))
        with _pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
