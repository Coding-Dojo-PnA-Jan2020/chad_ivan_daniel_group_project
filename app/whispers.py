"""Whispers: the encrypted feed."""

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.crypto import decrypt_message, encrypt_message
from app.forms import WhisperForm
from app.models import Follow, Like, Whisper

bp = Blueprint("whispers", __name__)


def _visible_author_ids() -> list[int]:
    """Whispers are end-to-end keyed per author, but the feed only shows
    whispers from yourself and people you follow."""
    rows = Follow.query.with_entities(Follow.followed_id).filter_by(
        follower_id=current_user.id
    )
    return [current_user.id] + [r.followed_id for r in rows]


@bp.route("/dashboard")
@login_required
def dashboard():
    whispers = (
        Whisper.query.filter(Whisper.author_id.in_(_visible_author_ids()))
        .order_by(Whisper.created_at.desc(), Whisper.id.desc())
        .all()
    )
    feed = []
    for w in whispers:
        plaintext = decrypt_message(w.body, w.author_id)
        if plaintext is None:
            continue  # ciphertext not decryptable with the current key — skip
        feed.append({"model": w, "body": plaintext})
    return render_template("whispers/dashboard.html", feed=feed, form=WhisperForm())


@bp.route("/whispers", methods=["POST"])
@login_required
def create():
    form = WhisperForm()
    if form.validate_on_submit():
        whisper = Whisper(
            body=encrypt_message(form.body.data.strip(), current_user.id),
            author_id=current_user.id,
        )
        db.session.add(whisper)
        db.session.commit()
        flash("Whisper posted! 🤫", "success")
    else:
        for errors in form.body.errors:
            flash(errors, "danger")
    return redirect(url_for("whispers.dashboard"))


@bp.route("/whispers/<int:whisper_id>/delete", methods=["POST"])
@login_required
def delete(whisper_id: int):
    whisper = db.session.get(Whisper, whisper_id)
    if whisper is None:
        abort(404)
    if whisper.author_id != current_user.id:
        abort(403)  # ownership enforced server-side
    db.session.delete(whisper)
    db.session.commit()
    flash("Whisper deleted.", "info")
    return redirect(url_for("whispers.dashboard"))


@bp.route("/whispers/<int:whisper_id>/like", methods=["POST"])
@login_required
def toggle_like(whisper_id: int):
    whisper = db.session.get(Whisper, whisper_id)
    if whisper is None:
        abort(404)
    existing = Like.query.filter_by(
        user_id=current_user.id, whisper_id=whisper_id
    ).first()
    if existing is not None:
        db.session.delete(existing)
    else:
        db.session.add(Like(user_id=current_user.id, whisper_id=whisper_id))
    db.session.commit()
    return redirect(request.referrer or url_for("whispers.dashboard"))
