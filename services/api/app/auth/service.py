import uuid
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.models import RefreshToken, User
from app.auth.security import (
    as_utc,
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    utcnow,
    verify_password,
)
from app.core.errors import UnauthorizedError
from app.core.settings import get_settings

# Verified against when the email is unknown, so timing doesn't reveal which emails exist.
_DUMMY_HASH = hash_password("timing-equaliser")


def _issue_refresh(db: Session, user_id: int, family_id: str) -> str:
    raw, digest = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=digest,
            family_id=family_id,
            expires_at=utcnow() + timedelta(days=get_settings().refresh_token_ttl_days),
        )
    )
    return raw


def login(db: Session, email: str, password: str) -> tuple[User, str, str]:
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    ok = verify_password(password, user.password_hash if user else _DUMMY_HASH)
    if not user or not ok or not user.is_active:
        raise UnauthorizedError("Invalid email or password")
    refresh = _issue_refresh(db, user.id, str(uuid.uuid4()))
    db.commit()
    return user, create_access_token(user.id), refresh


def _revoke_family(db: Session, family_id: str) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )


def refresh(db: Session, raw_token: str) -> tuple[User, str, str]:
    """Rotate: the presented token is revoked and a new one issued in the same family.

    Presenting an already-revoked token means theft/replay: the whole family is revoked.
    """
    row = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    )
    if row is None:
        raise UnauthorizedError("Invalid refresh token")
    if row.revoked_at is not None:
        _revoke_family(db, row.family_id)
        db.commit()
        raise UnauthorizedError("Invalid refresh token")
    if as_utc(row.expires_at) <= utcnow():
        raise UnauthorizedError("Refresh token expired")
    user = db.get(User, row.user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("Invalid refresh token")
    row.revoked_at = utcnow()
    new_raw = _issue_refresh(db, user.id, row.family_id)
    db.commit()
    return user, create_access_token(user.id), new_raw


def logout(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    row = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    )
    if row:
        _revoke_family(db, row.family_id)
        db.commit()
