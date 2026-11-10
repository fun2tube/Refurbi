"""Partner POS API (T17). Counter-scoped: a partner only sees/sells their own counter's stock.

No IMEI (only last 4), no cost, supplier or commission is ever returned.
"""

import re
from urllib.parse import quote

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.auth.models import User
from app.billing.models import Invoice
from app.billing.pdf import render_pdf, rupees
from app.billing.service import issue_invoice
from app.catalog.models import Brand, ProductModel, ProductVariant
from app.core.db import get_session
from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.settings import get_settings
from app.counters.models import Counter
from app.inventory.lifecycle import transition
from app.inventory.models import Device, DeviceStatus, LocationKind
from app.pos.models import Sale

router = APIRouter(prefix="/pos/counters/{counter_id}", tags=["pos"])
_stock = Depends(require_permission("counter.stock.read", counter_param="counter_id"))
_sell = Depends(require_permission("counter.sell", counter_param="counter_id"))
_sales = Depends(require_permission("sales.read", counter_param="counter_id"))


class SaleIn(BaseModel):
    device_id: int
    customer_name: str = Field(min_length=1, max_length=120)
    customer_phone: str = Field(pattern=r"^[6-9]\d{9}$")  # Indian mobile, 10 digits
    payment_mode: str = Field(pattern="^(CASH|UPI|CARD)$")
    payment_ref: str = Field(default="", max_length=60)


def upi_uri(amount_paise: int, note: str) -> str:
    st = get_settings()
    return (
        f"upi://pay?pa={quote(st.upi_id)}&pn={quote(st.upi_payee_name)}"
        f"&am={amount_paise // 100}.{amount_paise % 100:02d}&cu=INR&tn={quote(note)}"
    )


def whatsapp_link(phone: str, text: str) -> str:
    return f"https://wa.me/91{re.sub(r'\D', '', phone)[-10:]}?text={quote(text)}"


@router.get("/stock")
def stock(
    counter_id: int,
    q: str = "",
    user: User = _stock,
    db: Session = Depends(get_session),
) -> list[dict]:
    stmt = (
        select(Device, Brand.name, ProductModel.name, ProductVariant)
        .join(ProductVariant, ProductVariant.id == Device.variant_id)
        .join(ProductModel, ProductModel.id == ProductVariant.model_id)
        .join(Brand, Brand.id == ProductModel.brand_id)
        .where(
            Device.status == DeviceStatus.AVAILABLE.value,
            Device.location_kind == LocationKind.COUNTER.value,
            Device.counter_id == counter_id,
        )
        .order_by(Device.id.desc())
        .limit(100)
    )
    q = q.strip()
    if q:
        like = f"%{q.lower()}%"
        from sqlalchemy import func, or_

        stmt = stmt.where(
            or_(
                func.lower(ProductModel.name).like(like),
                func.lower(Brand.name).like(like),
                Device.imei_last4 == q,
            )
        )
    return [
        {
            "device_id": d.id,
            "brand": b,
            "model": m,
            "storage_gb": v.storage_gb,
            "color": v.color,
            "grade": d.grade,
            "battery_health": d.battery_health,
            "imei_last4": d.imei_last4,
            "price_paise": d.price_paise,
        }
        for d, b, m, v in db.execute(stmt)
    ]


def _sale_out(db: Session, s: Sale, inv: Invoice) -> dict:
    msg = (
        f"Thank you for your purchase! Invoice {inv.number} for {rupees(inv.total_paise)}. "
        "Please keep this for warranty."
    )
    out = {
        "sale_id": s.id,
        "invoice_id": inv.id,
        "invoice_number": inv.number,
        "invoice_pdf_url": f"/pos/counters/{s.counter_id}/invoices/{inv.id}/pdf",
        "total_paise": inv.total_paise,
        "payment_mode": s.payment_mode,
        "whatsapp_url": whatsapp_link(s.customer_phone, msg),
    }
    if s.payment_mode == "UPI":
        out["upi_uri"] = upi_uri(inv.total_paise, inv.number)
    return out


@router.post("/sales", status_code=201)
def sell(
    counter_id: int, body: SaleIn, user: User = _sell, db: Session = Depends(get_session)
) -> dict:
    c = db.get(Counter, counter_id)
    if c is None or not c.is_active:
        raise NotFoundError("Counter not found")
    d = db.scalar(select(Device).where(Device.id == body.device_id).with_for_update())
    if d is None or d.counter_id != counter_id or d.location_kind != LocationKind.COUNTER.value:
        raise NotFoundError("Device not found at this counter")
    if d.status != DeviceStatus.AVAILABLE.value:
        raise ConflictError("Device is not available for sale", code="device_not_available")
    if d.price_paise is None:
        raise AppError("Device has no price", code="no_price")
    price = d.price_paise
    mode = get_settings().default_gst_mode
    transition(db, d.id, DeviceStatus.SOLD, actor_user_id=user.id, reason=f"POS sale at {c.slug}")
    inv = issue_invoice(
        db,
        d.id,
        selling_paise=price,
        customer_name=body.customer_name,
        customer_phone=body.customer_phone,
        mode=mode,
        counter_id=counter_id,
    )
    s = Sale(
        device_id=d.id,
        counter_id=counter_id,
        invoice_id=inv.id,
        sold_by=user.id,
        customer_name=inv.customer_name,
        customer_phone=inv.customer_phone,
        price_paise=price,
        payment_mode=body.payment_mode,
        payment_ref=body.payment_ref.strip(),
    )
    db.add(s)
    db.commit()
    return _sale_out(db, s, inv)


@router.get("/sales")
def my_sales(
    counter_id: int, user: User = _sales, db: Session = Depends(get_session)
) -> list[dict]:
    rows = db.execute(
        select(Sale, Invoice)
        .join(Invoice, Invoice.id == Sale.invoice_id)
        .where(Sale.counter_id == counter_id)
        .order_by(Sale.id.desc())
        .limit(100)
    )
    return [
        {**_sale_out(db, s, i), "customer_name": s.customer_name, "created_at": s.created_at}
        for s, i in rows
    ]


@router.get("/invoices/{invoice_id}/pdf")
def invoice_pdf(
    counter_id: int, invoice_id: int, user: User = _sales, db: Session = Depends(get_session)
) -> Response:
    i = db.get(Invoice, invoice_id)
    if i is None or i.counter_id != counter_id:
        raise NotFoundError("Invoice not found")
    return Response(render_pdf(i), media_type="application/pdf")
