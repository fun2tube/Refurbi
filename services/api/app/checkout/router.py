from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.checkout import service
from app.checkout.models import Checkout, CheckoutItem
from app.core.db import get_session
from app.inventory.models import Device
from app.reservations.router import Email, _rate_limit

public = APIRouter(prefix="/public", tags=["checkout"])
Pin = Annotated[str, StringConstraints(pattern=r"^[1-9][0-9]{5}$")]


class CheckoutIn(BaseModel):
    unit_ids: list[int] = Field(min_length=1, max_length=service.MAX_ITEMS)
    name: str = Field(min_length=1, max_length=120)
    email: Email
    phone: str = Field(pattern=r"^[0-9+\- ]{8,15}$")
    address_line: str = Field(min_length=3, max_length=300)
    city: str = Field(min_length=2, max_length=80)
    pincode: Pin
    otp: str = Field(min_length=4, max_length=8)


class ItemOut(BaseModel):
    unit_id: int
    price_paise: int


class CheckoutOut(BaseModel):
    token: str
    status: str
    items: list[ItemOut]
    total_paise: int
    expires_at: datetime
    seconds_left: int
    hold_minutes: int = service.HOLD_MINUTES
    delivery: dict | None


def _out(db: Session, c: Checkout) -> CheckoutOut:
    items = db.scalars(select(CheckoutItem).where(CheckoutItem.checkout_id == c.id)).all()
    return CheckoutOut(
        token=c.token,
        status=c.status,
        items=[ItemOut(unit_id=i.device_id, price_paise=i.price_paise) for i in items],
        total_paise=c.total_paise,
        expires_at=c.expires_at,
        seconds_left=service.remaining_seconds(c) if c.status == "HOLD" else 0,
        delivery=service.delivery_estimate(c.pincode),
    )


@public.get("/delivery-estimate")
def delivery_estimate(pincode: str):
    est = service.delivery_estimate(pincode)
    if est is None:
        raise HTTPException(422, "Enter a valid 6-digit PIN code")
    return est


class CartItem(BaseModel):
    unit_id: int
    available: bool
    price_paise: int | None


@public.get("/cart", response_model=list[CartItem])
def cart_check(ids: str, db: Session = Depends(get_session)):
    """Re-validate cart contents: availability and current price only."""
    try:
        wanted = [int(x) for x in ids.split(",") if x][: service.MAX_ITEMS * 2]
    except ValueError:
        raise HTTPException(422, "Invalid ids") from None
    service.release_expired(db)
    found = {d.id: d for d in db.scalars(select(Device).where(Device.id.in_(wanted)))}
    out = []
    for i in wanted:
        d = found.get(i)
        ok = d is not None and d.status == "AVAILABLE" and d.price_paise is not None
        out.append(CartItem(unit_id=i, available=ok, price_paise=d.price_paise if ok else None))
    return out


@public.post("/checkout", response_model=CheckoutOut, status_code=201)
def create_checkout(body: CheckoutIn, request: Request, db: Session = Depends(get_session)):
    _rate_limit(f"co:{request.client.host if request.client else '?'}", 10)
    c = service.create_hold(
        db, body.unit_ids, body.model_dump(exclude={"unit_ids", "otp"}), body.otp
    )
    return _out(db, c)


@public.get("/checkout/{token}", response_model=CheckoutOut)
def get_checkout(token: str, db: Session = Depends(get_session)):
    return _out(db, service.get_by_token(db, token))


@public.post("/checkout/{token}/cancel", response_model=CheckoutOut)
def cancel_checkout(token: str, db: Session = Depends(get_session)):
    return _out(db, service.cancel(db, token))
