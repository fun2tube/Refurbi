from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.billing.models import Invoice
from app.billing.pdf import render_pdf
from app.catalog.models import ProductModel, ProductVariant
from app.core.db import get_session
from app.core.errors import NotFoundError
from app.inventory.models import Device
from app.orders import returns, service
from app.orders.courier import Courier, get_courier
from app.orders.models import Order, OrderItem, OrderStatusHistory, ReturnRequest
from app.payments.gateway import Gateway, get_gateway
from app.reservations.router import Email, _rate_limit
from app.reservations.service import norm_email, verify_otp
from app.warranty.models import Warranty

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
    invoice_number: str | None = None
    warranty_months: int | None = None
    warranty_ends_on: date | None = None
    warranty_active: bool | None = None
    return_status: str | None = None
    refund_paise: int | None = None


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
        select(
            OrderItem.price_paise,
            ProductModel.name,
            ProductVariant.storage_gb,
            Invoice.number,
            Warranty.months,
            Warranty.ends_on,
            ReturnRequest.status,
            ReturnRequest.refund_paise,
        )
        .join(Device, Device.id == OrderItem.device_id)
        .join(ProductVariant, ProductVariant.id == Device.variant_id)
        .join(ProductModel, ProductModel.id == ProductVariant.model_id)
        .outerjoin(Invoice, Invoice.device_id == OrderItem.device_id)
        .outerjoin(Warranty, Warranty.device_id == OrderItem.device_id)
        .outerjoin(ReturnRequest, ReturnRequest.order_item_id == OrderItem.id)
        .where(OrderItem.order_id == o.id)
    ).all()
    today = datetime.now(UTC).date()
    hist = db.scalars(
        select(OrderStatusHistory)
        .where(OrderStatusHistory.order_id == o.id)
        .order_by(OrderStatusHistory.id)
    ).all()
    return OrderOut(
        number=o.number, token=o.token, status=o.status, total_paise=o.total_paise,
        placed_at=o.created_at, carrier=o.carrier, tracking_no=o.tracking_no,
        items=[
            OrderItemOut(
                title=f"{n} {g}GB", price_paise=p, invoice_number=inv, warranty_months=m,
                warranty_ends_on=e, warranty_active=None if e is None else e >= today,
                return_status=rs, refund_paise=rp if rs == "REFUNDED" else None,
            )
            for p, n, g, inv, m, e, rs, rp in rows
        ],
        timeline=[TimelineOut(status=h.status, note=h.note, at=h.created_at) for h in hist],
    )  # fmt: skip


@public.get("/orders/{token}", response_model=OrderOut)
def track(token: str, db: Session = Depends(get_session)):
    o = db.scalar(select(Order).where(Order.token == token))
    if o is None:
        raise NotFoundError("Order not found")
    return _view(db, o)


@public.get("/orders/{token}/invoice.pdf")
def invoice_pdf(token: str, number: str, db: Session = Depends(get_session)) -> Response:
    """Customer's own invoice, gated by the unguessable order token + the invoice number
    (which must belong to a device in that order)."""
    o = db.scalar(select(Order).where(Order.token == token))
    inv = db.scalar(
        select(Invoice)
        .join(OrderItem, OrderItem.device_id == Invoice.device_id)
        .where(OrderItem.order_id == (o.id if o else -1), Invoice.number == number)
    )
    if o is None or inv is None:
        raise NotFoundError("Invoice not found")
    return Response(
        render_pdf(inv), media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{number.replace("/", "-")}.pdf"'},
    )  # fmt: skip


class ReturnIn(BaseModel):
    invoice_number: str = Field(min_length=3, max_length=40)
    reason: str = Field(min_length=3, max_length=500)


@public.post("/orders/{token}/returns", status_code=201)
def request_return(token: str, body: ReturnIn, db: Session = Depends(get_session)) -> dict:
    o = db.scalar(select(Order).where(Order.token == token))
    item = (
        db.scalar(
            select(OrderItem)
            .join(Invoice, Invoice.device_id == OrderItem.device_id)
            .where(OrderItem.order_id == o.id, Invoice.number == body.invoice_number.strip())
        )
        if o
        else None
    )
    if o is None or item is None:
        raise NotFoundError("Order item not found")
    r = returns.request_return(db, o, item, body.reason)
    return {"status": r.status}


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


class AdminOrderDetail(AdminOrder):
    items: list[OrderItemOut]
    timeline: list[TimelineOut]


@admin.get("/{order_id}", response_model=AdminOrderDetail, dependencies=[_perm])
def order_detail(order_id: int, db: Session = Depends(get_session)):
    o = db.get(Order, order_id)
    if o is None:
        raise NotFoundError("Order not found")
    v = _view(db, o)
    return AdminOrderDetail(**_adm(o).model_dump(), items=v.items, timeline=v.timeline)


@admin.post("/{order_id}/advance", response_model=AdminOrder)
def advance(
    order_id: int,
    db: Session = Depends(get_session),
    courier: Courier = Depends(get_courier),
    user=Depends(require_permission("orders.manage")),
):
    return _adm(service.advance(db, order_id, courier, getattr(user, "id", None)))


class AdminReturn(BaseModel):
    id: int
    order_number: str
    item: str
    invoice_number: str | None
    price_paise: int
    reason: str
    status: str
    refund_paise: int
    refund_ref: str | None
    admin_note: str
    created_at: datetime


returns_admin = APIRouter(prefix="/admin/returns", tags=["returns-admin"])


def _ret(db: Session, r: ReturnRequest) -> AdminReturn:
    row = db.execute(
        select(
            Order.number,
            OrderItem.price_paise,
            ProductModel.name,
            ProductVariant.storage_gb,
            Invoice.number,
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Device, Device.id == OrderItem.device_id)
        .join(ProductVariant, ProductVariant.id == Device.variant_id)
        .join(ProductModel, ProductModel.id == ProductVariant.model_id)
        .outerjoin(Invoice, Invoice.device_id == OrderItem.device_id)
        .where(OrderItem.id == r.order_item_id)
    ).one()
    return AdminReturn(
        id=r.id, order_number=row[0], price_paise=row[1], item=f"{row[2]} {row[3]}GB",
        invoice_number=row[4], reason=r.reason, status=r.status, refund_paise=r.refund_paise,
        refund_ref=r.refund_ref, admin_note=r.admin_note, created_at=r.created_at,
    )  # fmt: skip


class DecisionIn(BaseModel):
    note: str = Field(default="", max_length=300)


class RefundIn(BaseModel):
    amount_paise: int | None = Field(default=None, gt=0)


@returns_admin.get("", response_model=list[AdminReturn], dependencies=[_perm])
def list_returns(db: Session = Depends(get_session)):
    rows = db.scalars(select(ReturnRequest).order_by(ReturnRequest.id.desc()).limit(200))
    return [_ret(db, r) for r in rows]


@returns_admin.post("/{rid}/approve", response_model=AdminReturn)
def approve(rid: int, body: DecisionIn, db: Session = Depends(get_session), user=_perm):
    return _ret(db, returns.decide(db, rid, True, body.note, getattr(user, "id", None)))


@returns_admin.post("/{rid}/reject", response_model=AdminReturn)
def reject(rid: int, body: DecisionIn, db: Session = Depends(get_session), user=_perm):
    return _ret(db, returns.decide(db, rid, False, body.note, getattr(user, "id", None)))


@returns_admin.post("/{rid}/receive", response_model=AdminReturn)
def receive(rid: int, db: Session = Depends(get_session), user=_perm):
    return _ret(db, returns.receive(db, rid, getattr(user, "id", None)))


@returns_admin.post("/{rid}/refund", response_model=AdminReturn)
def refund(
    rid: int,
    body: RefundIn,
    db: Session = Depends(get_session),
    gw: Gateway = Depends(get_gateway),
    user=_perm,
):
    return _ret(db, returns.refund(db, rid, gw, body.amount_paise, getattr(user, "id", None)))
