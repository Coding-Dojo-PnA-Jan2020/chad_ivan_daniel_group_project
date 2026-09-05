"""Message encryption.

Each user's Fernet key is derived at runtime from the server SECRET_KEY and
the user's database id using HKDF-SHA256. Keys are never persisted anywhere,
so a database leak alone cannot decrypt whispers — you need the server's
secret as well. Rotating SECRET_KEY invalidates all existing ciphertexts,
which is the documented re-encryption procedure (see README).
"""

import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from flask import current_app

_PURPOSE = b"whisper-message-key-v1"


def _derive_key(user_id: int) -> bytes:
    secret = current_app.config["SECRET_KEY"].encode()
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=_PURPOSE + b":" + str(user_id).encode(),
    )
    return base64.urlsafe_b64encode(hkdf.derive(secret))


def _fernet(user_id: int) -> Fernet:
    return Fernet(_derive_key(user_id))


def encrypt_message(plaintext: str, author_id: int) -> str:
    """Encrypt a whisper. Returns the Fernet token as a str (stored in DB)."""
    return _fernet(author_id).encrypt(plaintext.encode()).decode()


def decrypt_message(token: str, author_id: int) -> str | None:
    """Decrypt a whisper. Returns None if the token is corrupt or the key
    changed (e.g. after a SECRET_KEY rotation without re-encryption)."""
    try:
        return _fernet(author_id).decrypt(token.encode()).decode()
    except (InvalidToken, ValueError):
        return None
