"""IMEI helpers: validation, encryption at rest (Fernet, rotation-ready) and a keyed hash for
uniqueness/lookup. Plaintext IMEI must never be logged or returned by public endpoints."""

import hashlib
import hmac
import re

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.core.settings import get_settings

_IMEI_RE = re.compile(r"^\d{15}$")


def normalise_imei(raw: str) -> str:
    imei = re.sub(r"[\s-]", "", raw)
    if not _IMEI_RE.match(imei) or not luhn_ok(imei):
        raise ValueError("Invalid IMEI")
    return imei


def luhn_ok(number: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _fernet() -> MultiFernet:
    keys = [k.strip() for k in get_settings().imei_encryption_keys.split(",") if k.strip()]
    return MultiFernet([Fernet(k) for k in keys])


def encrypt_imei(imei: str) -> str:
    return _fernet().encrypt(imei.encode()).decode()


def decrypt_imei(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        raise ValueError("IMEI cannot be decrypted with the configured keys") from None


def rotate_imei(token: str) -> str:
    """Re-encrypt under the newest key (used by the key-rotation procedure, T34)."""
    return _fernet().rotate(token.encode()).decode()


def hash_imei(imei: str) -> str:
    key = get_settings().imei_hash_key.encode()
    return hmac.new(key, imei.encode(), hashlib.sha256).hexdigest()
