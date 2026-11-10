import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.checkout import service as checkout_service
from app.checkout.models import Checkout, CheckoutItem
from app.core.errors import ConflictError
from app.inventory.lifecycle import transition
from app.inventory.models import Device, DeviceStatus
from app.payments.gateway import Gateway
from app.payments.models import Payment, PaymentEvent


def start_payment(db: Session, token: str, gateway: Gateway) -> tuple[Payment, dict]:
    c = checkout_service.get_by_token(db, token)  # also expires stale holds
    if c.status != "HOLD":
        raise ConflictError("This checkout is not active")
    order = gateway.create_order(c.total_paise, f"co{c.id}")
    p = Payment(checkout_id=c.id, gateway=gateway.name, gateway_order_id=order["order_id"],
                amount_paise=c.total_paise)  # fmt: skip
    db.add(p)
    db.commit()
    return p, order


def _mark_paid(db: Session, p: Payment, payment_id: str | None) -> None:
    c = db.get(Checkout, p.checkout_id)
    p.gateway_payment_id = payment_id
    p.paid_at = datetime.now(UTC)
    if c.status == "HOLD":
        p.status, c.status = "PAID", "PAID"
        return
    if c.status == "EXPIRED":  # paid after the hold lapsed: re-take the phones if still free
        devs = [
            db.get(Device, i.device_id)
            for i in db.scalars(select(CheckoutItem).where(CheckoutItem.checkout_id == c.id))
        ]
        if all(d is not None and d.status == DeviceStatus.AVAILABLE.value for d in devs):
            for d in devs:
                transition(db, d.id, DeviceStatus.RESERVED, reason="late payment re-hold")
            p.status, c.status = "PAID", "PAID"
            return
    p.status = "REFUND_DUE"  # money received but phones gone: founder must refund (T32)


def handle_event(db: Session, event_id: str, body: bytes) -> str:
    """Process one verified webhook. Returns 'processed' | 'duplicate' | 'ignored'."""
    data = json.loads(body)
    etype = str(data.get("event", ""))
    db.add(PaymentEvent(event_id=event_id[:80], event_type=etype[:60]))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return "duplicate"
    entity = data.get("payload", {}).get("payment", {}).get("entity", {})
    p = db.scalar(select(Payment).where(Payment.gateway_order_id == entity.get("order_id")))
    if p is None or etype not in ("payment.captured", "payment.failed"):
        db.commit()
        return "ignored"
    if etype == "payment.captured" and p.status == "CREATED":
        if entity.get("amount") != p.amount_paise:
            p.status = "FAILED"  # amount mismatch: never fulfil
        else:
            _mark_paid(db, p, entity.get("id"))
    elif etype == "payment.failed" and p.status == "CREATED":
        p.status = "FAILED"
    db.commit()
    return "processed"
