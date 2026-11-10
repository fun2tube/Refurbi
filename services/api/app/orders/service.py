import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.checkout.models import Checkout, CheckoutItem
from app.core.errors import ConflictError, NotFoundError
from app.inventory.lifecycle import transition
from app.inventory.models import DeviceStatus
from app.orders.courier import Courier
from app.orders.models import Order, OrderItem, OrderStatusHistory

FLOW = {"PLACED": "PACKED", "PACKED": "SHIPPED", "SHIPPED": "DELIVERED"}


def _log(db: Session, o: Order, status: str, note: str = "", actor: int | None = None) -> None:
    db.add(OrderStatusHistory(order_id=o.id, status=status, note=note, actor_user_id=actor))


def create_from_checkout(db: Session, c: Checkout) -> Order:
    """Called when a checkout is paid. Idempotent per checkout. Caller commits."""
    existing = db.scalar(select(Order).where(Order.checkout_id == c.id))
    if existing:
        return existing
    o = Order(
        number="RO-" + secrets.token_hex(3).upper(),
        token=secrets.token_urlsafe(24),
        checkout_id=c.id,
        email=c.email,
        customer_name=c.customer_name,
        phone=c.phone,
        address_line=c.address_line,
        city=c.city,
        pincode=c.pincode,
        total_paise=c.total_paise,
    )
    db.add(o)
    db.flush()
    for it in db.scalars(select(CheckoutItem).where(CheckoutItem.checkout_id == c.id)):
        db.add(OrderItem(order_id=o.id, device_id=it.device_id, price_paise=it.price_paise))
        transition(db, it.device_id, DeviceStatus.SOLD, reason=f"online order {o.number}")
    _log(db, o, "PLACED", "Payment received")
    return o


def advance(db: Session, order_id: int, courier: Courier, actor: int | None) -> Order:
    o = db.get(Order, order_id)
    if o is None:
        raise NotFoundError("Order not found")
    nxt = FLOW.get(o.status)
    if nxt is None:
        raise ConflictError(f"Order is already {o.status}")
    note = ""
    if nxt == "SHIPPED":
        s = courier.create_shipment(o.number, o.pincode)
        o.carrier, o.tracking_no = s["carrier"], s["tracking_no"]
        note = f"{o.carrier} {o.tracking_no}"
    o.status = nxt
    _log(db, o, nxt, note, actor)
    db.commit()
    return o
