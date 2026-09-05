"""Database models."""

from datetime import UTC, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(45), nullable=False)
    last_name = db.Column(db.String(45), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(255))  # uploaded filename; None -> generated avatar
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    whispers = db.relationship(
        "Whisper", back_populates="author", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_following(self, other: "User") -> bool:
        return (
            Follow.query.filter_by(follower_id=self.id, followed_id=other.id).first()
            is not None
        )

    def __repr__(self) -> str:  # never log secrets
        return f"<User id={self.id} email={self.email!r}>"


class Whisper(db.Model):
    __tablename__ = "whispers"

    id = db.Column(db.Integer, primary_key=True)
    # Fernet ciphertext — the database never sees plaintext.
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    author = db.relationship("User", back_populates="whispers")
    likes = db.relationship(
        "Like", back_populates="whisper", cascade="all, delete-orphan"
    )

    @property
    def like_count(self) -> int:
        return len(self.likes)

    def liked_by(self, user_id: int) -> bool:
        return any(like.user_id == user_id for like in self.likes)


class Follow(db.Model):
    __tablename__ = "follows"

    follower_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    followed_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    follower = db.relationship("User", foreign_keys=[follower_id])
    followed = db.relationship("User", foreign_keys=[followed_id])


class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    whisper_id = db.Column(
        db.Integer, db.ForeignKey("whispers.id", ondelete="CASCADE"), nullable=False
    )
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    whisper = db.relationship("Whisper", back_populates="likes")

    __table_args__ = (db.UniqueConstraint("user_id", "whisper_id"),)


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
