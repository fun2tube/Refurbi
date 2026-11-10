"""Returns/refunds (T32). Device status changes go through the lifecycle service."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.settings import get_settings
from app.inventory.lifecycle import transition
from app.inventory.models import DeviceStatus
from app.orders.models import Order, OrderItem, OrderStatusHistory, ReturnRequest
from app.payments.gateway import Gateway
from app.payments.models import Payment
from app.warranty.models import Warranty


def request_return(db: Session, o: Order, item: OrderItem, reason: str) -> ReturnRequest:
    if o.status != "DELIVERED":
        raise ConflictError("Returns can be requested once the order is delivered")
    delivered = db.scalar(
        select(OrderStatusHistory.created_at)
        .where(OrderStatusHistory.order_id == o.id, OrderStatusHistory.status == "DELIVERED")
        .order_by(OrderStatusHistory.id.desc())
    )
    window = timedelta(days=get_settings().return_window_days)
    if delivered is not None:
        if delivered.tzinfo is None:
            delivered = delivered.replace(tzinfo=UTC)
        if datetime.now(UTC) > delivered + window:
            raise AppError("The return window for this order has closed", code="return_window")
    if db.scalar(select(ReturnRequest.id).where(ReturnRequest.order_item_id == item.id)):
        raise ConflictError(
            "A return was already requested for this item", code="already_requested"
        )
    r = ReturnRequest(order_item_id=item.id, order_id=o.id, reason=reason.strip())
    db.add(r)
    db.commit()
    return r


def _get(db: Session, rid: int) -> ReturnRequest:
    r = db.get(ReturnRequest, rid)
    if r is None:
        raise NotFoundError("Return not found")
    return r


def _expect(r: ReturnRequest, *states: str) -> None:
    if r.status not in states:
        raise ConflictError(f"Return is {r.status}; expected {' or '.join(states)}")


def decide(db: Session, rid: int, approve: bool, note: str, actor: int | None) -> ReturnRequest:
    r = _get(db, rid)
    _expect(r, "REQUESTED")
    r.status = "APPROVED" if approve else "REJECTED"
    r.admin_note = note[:300]
    db.commit()
    return r


def receive(db: Session, rid: int, actor: int | None) -> ReturnRequest:
    """Device is back: SOLD -> RETURNED through the lifecycle (re-QC before it can be resold)."""
    r = _get(db, rid)
    _expect(r, "APPROVED")
    item = db.get(OrderItem, r.order_item_id)
    transition(
        db, item.device_id, DeviceStatus.RETURNED, actor_user_id=actor, reason=f"return #{r.id}"
    )
    r.status = "RECEIVED"
    db.commit()
    return r


def refund(
    db: Session, rid: int, gw: Gateway, amount_paise: int | None, actor: int | None
) -> ReturnRequest:
    r = _get(db, rid)
    _expect(r, "RECEIVED")
    item = db.get(OrderItem, r.order_item_id)
    amount = item.price_paise if amount_paise is None else amount_paise
    if amount <= 0 or amount > item.price_paise:
        raise AppError("Refund must be between Rs 1 and the item price", code="invalid_refund")
    o = db.get(Order, r.order_id)
    pay = db.scalar(
        select(Payment).where(Payment.checkout_id == o.checkout_id, Payment.status == "PAID")
    )
    r.refund_ref = gw.refund(pay.gateway_payment_id if pay else None, amount)
    r.refund_paise, r.status = amount, "REFUNDED"
    w = db.scalar(select(Warranty).where(Warranty.device_id == item.device_id))
    if w is not None:  # refunded device no longer carries the customer's warranty
        w.ends_on = min(w.ends_on, datetime.now(UTC).date() - timedelta(days=1))
    db.commit()
    return r
