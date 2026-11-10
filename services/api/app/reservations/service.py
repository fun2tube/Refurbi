import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.settings import get_settings
from app.counters.models import Counter
from app.inventory.lifecycle import transition
from app.inventory.models import Device, DeviceStatus
from app.reservations.email import EmailSender
from app.reservations.models import EmailOtp, Reservation

MAX_ATTEMPTS = 5


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _hash(email: str, code: str) -> str:
    key = get_settings().jwt_secret.encode()
    return hmac.new(key, f"{email}:{code}".encode(), hashlib.sha256).hexdigest()


def norm_email(email: str) -> str:
    return email.strip().lower()


def send_otp(db: Session, email: str, sender: EmailSender) -> str:
    email = norm_email(email)
    code = f"{secrets.randbelow(10**6):06d}"
    ttl = get_settings().otp_ttl_minutes
    db.add(
        EmailOtp(
            email=email, code_hash=_hash(email, code), expires_at=_now() + timedelta(minutes=ttl)
        )
    )
    db.commit()
    sender.send(
        email,
        "Your Refurbi verification code",
        f"Your code is {code}. It expires in {ttl} minutes.",
    )
    return code


def verify_otp(db: Session, email: str, code: str) -> None:
    email = norm_email(email)
    otp = db.scalar(
        select(EmailOtp)
        .where(EmailOtp.email == email, EmailOtp.used.is_(False))
        .order_by(EmailOtp.id.desc())
        .limit(1)
    )
    bad = AppError("Invalid or expired code", code="invalid_otp")
    bad.status_code = 400
    if otp is None or _aware(otp.expires_at) < _now() or otp.attempts >= MAX_ATTEMPTS:
        raise bad
    otp.attempts += 1
    if not hmac.compare_digest(otp.code_hash, _hash(email, code.strip())):
        db.commit()
        raise bad
    otp.used = True


def release_expired(db: Session, actor_user_id: int | None = None) -> int:
    rows = db.scalars(
        select(Reservation).where(Reservation.status == "ACTIVE", Reservation.expires_at < _now())
    ).all()
    for r in rows:
        d = db.get(Device, r.device_id)
        if d is not None and d.status == DeviceStatus.RESERVED.value:
            transition(db, d.id, DeviceStatus.AVAILABLE, actor_user_id=actor_user_id,
                       reason="reservation expired")  # fmt: skip
        r.status = "EXPIRED"
    db.commit()
    return len(rows)


def reserve(
    db: Session, unit_id: int, name: str, email: str, code: str, sender: EmailSender
) -> tuple[Reservation, Counter | None]:
    release_expired(db)
    d = db.scalar(select(Device).where(Device.id == unit_id).with_for_update())
    if d is None or d.status != DeviceStatus.AVAILABLE.value or d.price_paise is None:
        raise NotFoundError("This unit is no longer available")
    counter = db.get(Counter, d.counter_id) if d.counter_id else None
    if counter is not None and not (counter.is_verified and counter.is_active):
        raise NotFoundError("This unit is no longer available")
    verify_otp(db, email, code)
    transition(db, d.id, DeviceStatus.RESERVED, reason="store pickup reservation")
    r = Reservation(
        code=secrets.token_hex(3).upper(),
        device_id=d.id,
        counter_id=d.counter_id,
        customer_name=name.strip(),
        email=norm_email(email),
        expires_at=_now() + timedelta(hours=get_settings().reservation_hours),
    )
    db.add(r)
    db.commit()
    where = counter.name if counter else "our warehouse pickup point"
    sender.send(
        r.email,
        "Your Refurbi reservation",
        f"Reservation {r.code} is held at {where} until {r.expires_at:%Y-%m-%d %H:%M} UTC. "
        "Show this code at the store. Payment is made at the store.",
    )
    return r, counter


def cancel(db: Session, reservation_id: int, actor_user_id: int | None) -> Reservation:
    r = db.get(Reservation, reservation_id)
    if r is None:
        raise NotFoundError("Reservation not found")
    if r.status != "ACTIVE":
        raise ConflictError("Reservation is not active")
    transition(db, r.device_id, DeviceStatus.AVAILABLE, actor_user_id=actor_user_id,
               reason="reservation cancelled")  # fmt: skip
    r.status = "CANCELLED"
    db.commit()
    return r
