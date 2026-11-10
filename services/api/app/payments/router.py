import json
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.settings import get_settings
from app.payments import service
from app.payments.gateway import Gateway, get_gateway, verify_signature
from app.payments.models import Payment
from app.reservations.router import _rate_limit

public = APIRouter(prefix="/public/payments", tags=["payments"])


@public.post("/{token}/start")
def start(
    token: str,
    request: Request,
    db: Session = Depends(get_session),
    gw: Gateway = Depends(get_gateway),
):
    _rate_limit(f"pay:{request.client.host if request.client else '?'}", 20)
    p, order = service.start_payment(db, token, gw)
    return {"gateway": p.gateway, "order_id": order["order_id"], "key_id": order["key_id"],
            "amount_paise": p.amount_paise, "currency": "INR"}  # fmt: skip


@public.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_session)):
    body = await request.body()
    if not verify_signature(body, request.headers.get("x-razorpay-signature")):
        raise HTTPException(400, "Invalid signature")
    event_id = request.headers.get("x-razorpay-event-id")
    if not event_id:
        raise HTTPException(400, "Missing event id")
    try:
        return {"result": service.handle_event(db, event_id, body)}
    except (ValueError, AttributeError):
        raise HTTPException(400, "Malformed event") from None


@public.post("/fake/{order_id}/pay")
def fake_pay(order_id: str, db: Session = Depends(get_session)):
    """Demo only: simulate the gateway capturing a payment (fake gateway, non-production)."""
    s = get_settings()
    p = db.query(Payment).filter(Payment.gateway_order_id == order_id).first()
    if s.razorpay_key_id or s.app_env not in ("dev", "preview", "test") or p is None:
        raise HTTPException(404, "Not found")
    if p.gateway != "fake":
        raise HTTPException(404, "Not found")
    body = json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {
        "id": f"fake_pay_{secrets.token_hex(6)}", "order_id": order_id,
        "amount": p.amount_paise}}}}).encode()  # fmt: skip
    service.handle_event(db, f"fake_evt_{secrets.token_hex(8)}", body)
    db.refresh(p)
    return {"status": p.status}
