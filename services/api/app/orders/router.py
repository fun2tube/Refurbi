from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.catalog.models import ProductModel, ProductVariant
from app.core.db import get_session
from app.core.errors import NotFoundError
from app.inventory.models import Device
from app.orders import service
from app.orders.courier import Courier, get_courier
from app.orders.models import Order, OrderItem, OrderStatusHistory
from app.reservations.router import Email, _rate_limit
from app.reservations.service import norm_email, verify_otp

public = APIRouter(prefix="/public", tags=["orders"])
admin = APIRouter(prefix="/admin/orders", tags=["orders-admin"])
_perm = Depends(require_permission("orders.manage"))


class TimelineOut(BaseModel):
    status: str
    note: str
    at: datetime


class OrderItemOut(BaseModel):
    title: str
    price_paise: int


class OrderOut(BaseModel):
    number: str
    token: str
    status: str
    total_paise: int
    placed_at: datetime
    carrier: str | None
    tracking_no: str | None
    items: list[OrderItemOut]
    timeline: list[TimelineOut]


def _view(db: Session, o: Order) -> OrderOut:
    rows = db.execute(
        select(OrderItem.price_paise, ProductModel.name, ProductVariant.storage_gb)
        .join(Device, Device.id == OrderItem.device_id)
        .join(ProductVariant, ProductVariant.id == Device.variant_id)
        .join(ProductModel, ProductModel.id == ProductVariant.model_id)
        .where(OrderItem.order_id == o.id)
    ).all()
    hist = db.scalars(
        select(OrderStatusHistory)
        .where(OrderStatusHistory.order_id == o.id)
        .order_by(OrderStatusHistory.id)
    ).all()
    return OrderOut(
        number=o.number, token=o.token, status=o.status, total_paise=o.total_paise,
        placed_at=o.created_at, carrier=o.carrier, tracking_no=o.tracking_no,
        items=[OrderItemOut(title=f"{n} {g}GB", price_paise=p) for p, n, g in rows],
        timeline=[TimelineOut(status=h.status, note=h.note, at=h.created_at) for h in hist],
    )  # fmt: skip


@public.get("/orders/{token}", response_model=OrderOut)
def track(token: str, db: Session = Depends(get_session)):
    o = db.scalar(select(Order).where(Order.token == token))
    if o is None:
        raise NotFoundError("Order not found")
    return _view(db, o)


class AccountIn(BaseModel):
    email: Email
    otp: str


@public.post("/account/orders", response_model=list[OrderOut])
def my_orders(body: AccountIn, request: Request, db: Session = Depends(get_session)):
    _rate_limit(f"ac:{request.client.host if request.client else '?'}", 15)
    verify_otp(db, body.email, body.otp)
    db.commit()
    rows = db.scalars(
        select(Order)
        .where(Order.email == norm_email(body.email))
        .order_by(Order.id.desc())
        .limit(50)
    ).all()
    return [_view(db, o) for o in rows]


class AdminOrder(BaseModel):
    id: int
    number: str
    status: str
    total_paise: int
    customer_name: str
    email: str
    phone: str
    address: str
    carrier: str | None
    tracking_no: str | None
    created_at: datetime


def _adm(o: Order) -> AdminOrder:
    return AdminOrder(
        id=o.id, number=o.number, status=o.status, total_paise=o.total_paise,
        customer_name=o.customer_name, email=o.email, phone=o.phone,
        address=f"{o.address_line}, {o.city} {o.pincode}", carrier=o.carrier,
        tracking_no=o.tracking_no, created_at=o.created_at,
    )  # fmt: skip


@admin.get("", response_model=list[AdminOrder], dependencies=[_perm])
def list_orders(status: str | None = None, db: Session = Depends(get_session)):
    stmt = select(Order).order_by(Order.id.desc()).limit(200)
    if status:
        stmt = stmt.where(Order.status == status.upper())
    return [_adm(o) for o in db.scalars(stmt)]


@admin.post("/{order_id}/advance", response_model=AdminOrder)
def advance(
    order_id: int,
    db: Session = Depends(get_session),
    courier: Courier = Depends(get_courier),
    user=Depends(require_permission("orders.manage")),
):
    return _adm(service.advance(db, order_id, courier, getattr(user, "id", None)))
