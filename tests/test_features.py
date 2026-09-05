"""Functional coverage: whispers CRUD, follows, bio, avatars, profiles."""

import io


class TestWhispers:
    def test_create_and_show(self, logged_in_client, db):
        resp = logged_in_client.post(
            "/whispers", data={"body": "this is my secret whisper"}, follow_redirects=True
        )
        assert b"this is my secret whisper" in resp.data

    def test_body_encrypted_at_rest(self, logged_in_client, db, user):
        from app.models import Whisper

        logged_in_client.post("/whispers", data={"body": "plaintext visible?"})
        row = Whisper.query.one()
        assert "plaintext visible?" not in row.body
        assert row.body != ""

    def test_too_short_rejected(self, logged_in_client):
        resp = logged_in_client.post(
            "/whispers", data={"body": "hi"}, follow_redirects=True
        )
        assert b"5-280 characters" in resp.data

    def test_delete_own(self, logged_in_client, db, user):
        from app.models import Whisper
        from tests.conftest import make_whisper

        w = make_whisper(db, user)
        resp = logged_in_client.post(f"/whispers/{w.id}/delete", follow_redirects=True)
        assert b"Whisper deleted" in resp.data
        assert Whisper.query.count() == 0

    def test_like_toggle(self, logged_in_client, db, user):
        from app.models import Like
        from tests.conftest import make_whisper

        w = make_whisper(db, user)
        logged_in_client.post(f"/whispers/{w.id}/like")
        assert Like.query.count() == 1
        logged_in_client.post(f"/whispers/{w.id}/like")
        assert Like.query.count() == 0

    def test_missing_whisper_404(self, logged_in_client):
        assert logged_in_client.post("/whispers/9999/delete").status_code == 404


class TestFollows:
    def test_follow_unfollow(self, logged_in_client, db, user, other_user):
        from app.models import Follow

        logged_in_client.post(f"/users/{other_user.id}/follow")
        assert Follow.query.count() == 1
        logged_in_client.post(f"/users/{other_user.id}/unfollow")
        assert Follow.query.count() == 0

    def test_double_follow_no_duplicate(self, logged_in_client, db, other_user):
        from app.models import Follow

        logged_in_client.post(f"/users/{other_user.id}/follow")
        logged_in_client.post(f"/users/{other_user.id}/follow")
        assert Follow.query.count() == 1


class TestBioAndProfile:
    def test_bio_update(self, logged_in_client, user):
        resp = logged_in_client.post(
            "/account/bio", data={"bio": "ninja by night"}, follow_redirects=True
        )
        assert b"Bio updated" in resp.data
        assert user.bio == "ninja by night"

    def test_bio_too_long_rejected(self, logged_in_client, user):
        resp = logged_in_client.post("/account/bio", data={"bio": "x" * 501})
        assert b"Bio updated" not in resp.data

    def test_profile_page(self, logged_in_client, other_user):
        resp = logged_in_client.get(f"/users/{other_user.id}")
        assert b"John Smith" in resp.data

    def test_profile_404(self, logged_in_client):
        assert logged_in_client.get("/users/9999").status_code == 404

    def test_people_page(self, logged_in_client, other_user):
        resp = logged_in_client.get("/ninjas")
        assert b"John Smith" in resp.data


class TestHealth:
    def test_health_public(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json() == {"status": "ok"}


class TestAvatar:
    def _png_bytes(self):
        import io

        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color=(200, 30, 30)).save(buf, format="PNG")
        buf.seek(0)
        return buf

    def test_upload_png(self, logged_in_client, user, app):
        resp = logged_in_client.post(
            "/account/avatar",
            data={"file": (self._png_bytes(), "me.png")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert b"Avatar updated" in resp.data
        assert user.avatar and user.avatar.endswith(".png")

    def test_reject_non_image(self, logged_in_client, user):
        fake = io.BytesIO(b"#!/bin/sh\nrm -rf / # not an image")
        resp = logged_in_client.post(
            "/account/avatar",
            data={"file": (fake, "evil.png")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert b"could not be processed" in resp.data or b"must be a JPEG" in resp.data
        assert user.avatar is None

    def test_oversize_rejected(self, app, logged_in_client):
        app.config["MAX_CONTENT_LENGTH"] = 1024  # 1 KB cap for the test
        big = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 10_000)
        resp = logged_in_client.post(
            "/account/avatar",
            data={"file": (big, "big.png")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 413

    def test_generated_avatar_when_none(self, client, user):
        from app import avatar_url

        with client.application.test_request_context():
            url = avatar_url(user)
            assert url.startswith("https://api.dicebear.com/")
        assert user.avatar is None or user.avatar == ""
