"""User profiles, follows, bio and avatar management."""

import secrets
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from PIL import Image
from werkzeug.utils import secure_filename

from app import db
from app.crypto import decrypt_message
from app.forms import BioForm, WhisperForm
from app.models import Follow, User, Whisper

bp = Blueprint("users", __name__)

IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@bp.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename: str):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@bp.route("/ninjas")
@login_required
def people():
    users = User.query.filter(User.id != current_user.id).order_by(User.first_name).all()
    return render_template("users/people.html", users=users)


@bp.route("/users/<int:user_id>")
@login_required
def profile(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    whispers = (
        Whisper.query.filter_by(author_id=user_id)
        .order_by(Whisper.created_at.desc(), Whisper.id.desc())
        .all()
    )
    feed = []
    for w in whispers:
        plaintext = decrypt_message(w.body, w.author_id)
        if plaintext is not None:
            feed.append({"model": w, "body": plaintext})
    followers = Follow.query.filter_by(followed_id=user_id).count()
    following = Follow.query.filter_by(follower_id=user_id).count()
    is_following = current_user.is_following(user) if user_id != current_user.id else False
    bio_form = BioForm(bio=user.bio or "")
    return render_template(
        "users/profile.html",
        profile_user=user,
        feed=feed,
        followers=followers,
        following=following,
        is_following=is_following,
        bio_form=bio_form,
        whisper_form=WhisperForm(),
    )


@bp.route("/users/<int:user_id>/follow", methods=["POST"])
@login_required
def follow(user_id: int):
    _set_follow(user_id, add=True)
    return redirect(request.referrer or url_for("users.people"))


@bp.route("/users/<int:user_id>/unfollow", methods=["POST"])
@login_required
def unfollow(user_id: int):
    _set_follow(user_id, add=False)
    return redirect(request.referrer or url_for("users.people"))


def _set_follow(user_id: int, *, add: bool) -> None:
    if user_id == current_user.id:
        abort(403)  # cannot follow yourself
    if db.session.get(User, user_id) is None:
        abort(404)
    existing = Follow.query.filter_by(
        follower_id=current_user.id, followed_id=user_id
    ).first()
    if add and existing is None:
        db.session.add(Follow(follower_id=current_user.id, followed_id=user_id))
    elif not add and existing is not None:
        db.session.delete(existing)
    db.session.commit()


@bp.route("/account/bio", methods=["POST"])
@login_required
def update_bio():
    form = BioForm()
    if form.validate_on_submit():
        current_user.bio = form.bio.data.strip()
        db.session.commit()
        flash("Bio updated ✨", "success")
    else:
        for errors in form.bio.errors:
            flash(errors, "danger")
    return redirect(request.referrer or url_for("whispers.dashboard"))


@bp.route("/account/avatar", methods=["POST"])
@login_required
def upload_avatar():
    file = request.files.get("file")
    if file is None or file.filename == "":
        flash("Please choose an image to upload.", "danger")
        return redirect(url_for("users.profile", user_id=current_user.id))

    header = file.stream.read(16)
    file.stream.seek(0)
    ext = _sniff_extension(header, file.content_type)
    if ext is None:
        flash("Uploads must be a JPEG, PNG or WebP image.", "danger")
        return redirect(url_for("users.profile", user_id=current_user.id))

    filename = f"{current_user.id}_{secrets.token_hex(8)}{ext}"
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(file.stream) as img:
            img.load()  # full decode — rejects files that only look like images
            if ext == ".jpg":
                img = img.convert("RGB")
            img.thumbnail((512, 512))
            img.save(upload_dir / filename)
    except Exception:
        flash("That file could not be processed as an image.", "danger")
        return redirect(url_for("users.profile", user_id=current_user.id))

    if current_user.avatar:
        (upload_dir / secure_filename(current_user.avatar)).unlink(missing_ok=True)
    current_user.avatar = filename
    db.session.commit()
    flash("Avatar updated 🖼️", "success")
    return redirect(url_for("users.profile", user_id=current_user.id))


def _sniff_extension(header: bytes, declared_type: str) -> str | None:
    """Magic-byte sniffing first; the declared content type is only a fallback."""
    if header.startswith(b"\xff\xd8\xff"):
        return IMAGE_TYPES["image/jpeg"]
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return IMAGE_TYPES["image/png"]
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return IMAGE_TYPES["image/webp"]
    return IMAGE_TYPES.get(declared_type)
