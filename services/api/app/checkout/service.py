import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.checkout.models import Checkout, CheckoutItem
from app.core.errors import ConflictError, NotFoundError
from app.counters.models import Counter
from app.inventory.lifecycle import transition
from app.inventory.models import Device, DeviceStatus
from app.reservations.service import norm_email, verify_otp

HOLD_MINUTES = 15
MAX_ITEMS = 5

# Stub: indicative delivery days by first PIN digit (postal zone). Replaced by a courier
# adapter with real serviceability in T31.
_ZONE_DAYS = {"1": (3, 5), "2": (3, 5), "3": (4, 6), "4": (3, 5), "5": (3, 5),
              "6": (4, 6), "7": (4, 7), "8": (4, 7)}  # fmt: skip


def delivery_estimate(pincode: str) -> dict | None:
    if len(pincode) != 6 or not pincode.isdigit() or pincode[0] == "0":
        return None
    lo, hi = _ZONE_DAYS.get(pincode[0], (5, 8))
    return {"pincode": pincode, "min_days": lo, "max_days": hi, "estimate_only": True}


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _release(db: Session, c: Checkout, status: str, reason: str) -> None:
    for it in db.scalars(select(CheckoutItem).where(CheckoutItem.checkout_id == c.id)):
        d = db.get(Device, it.device_id)
        if d is not None and d.status == DeviceStatus.RESERVED.value:
            transition(db, d.id, DeviceStatus.AVAILABLE, reason=reason)
    c.status = status


def release_expired(db: Session) -> int:
    rows = db.scalars(
        select(Checkout).where(Checkout.status == "HOLD", Checkout.expires_at < _now())
    ).all()
    for c in rows:
        _release(db, c, "EXPIRED", "checkout hold expired")
    db.commit()
    return len(rows)


def create_hold(db: Session, unit_ids: list[int], customer: dict, code: str) -> Checkout:
    release_expired(db)
    ids = sorted(set(unit_ids))
    if not ids or len(ids) > MAX_ITEMS:
        raise ConflictError(f"Choose between 1 and {MAX_ITEMS} phones")
    if delivery_estimate(customer["pincode"]) is None:
        raise ConflictError("Enter a valid 6-digit PIN code")
    # Lock rows in id order so concurrent carts cannot deadlock.
    devices = db.scalars(select(Device).where(Device.id.in_(ids)).order_by(Device.id)
                         .with_for_update()).all()  # fmt: skip
    if len(devices) != len(ids):
        raise NotFoundError("A phone in your cart is no longer available")
    for d in devices:
        counter = db.get(Counter, d.counter_id) if d.counter_id else None
        ok_counter = counter is None or (counter.is_verified and counter.is_active)
        if d.status != DeviceStatus.AVAILABLE.value or d.price_paise is None or not ok_counter:
            raise NotFoundError("A phone in your cart is no longer available")
    verify_otp(db, customer["email"], code)
    for d in devices:
        transition(db, d.id, DeviceStatus.RESERVED, reason="online checkout hold")
    c = Checkout(
        token=secrets.token_urlsafe(24),
        customer_name=customer["name"].strip(),
        email=norm_email(customer["email"]),
        phone=customer["phone"].strip(),
        address_line=customer["address_line"].strip(),
        city=customer["city"].strip(),
        pincode=customer["pincode"],
        total_paise=sum(d.price_paise for d in devices),
        expires_at=_now() + timedelta(minutes=HOLD_MINUTES),
    )
    db.add(c)
    db.flush()
    for d in devices:
        db.add(CheckoutItem(checkout_id=c.id, device_id=d.id, price_paise=d.price_paise))
    db.commit()
    return c


def get_by_token(db: Session, token: str) -> Checkout:
    release_expired(db)
    c = db.scalar(select(Checkout).where(Checkout.token == token))
    if c is None:
        raise NotFoundError("Checkout not found")
    return c


def cancel(db: Session, token: str) -> Checkout:
    c = get_by_token(db, token)
    if c.status != "HOLD":
        raise ConflictError("Checkout is not active")
    _release(db, c, "CANCELLED", "checkout cancelled")
    db.commit()
    return c


def remaining_seconds(c: Checkout) -> int:
    return max(0, int((_aware(c.expires_at) - _now()).total_seconds()))
