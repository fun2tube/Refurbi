"""Warranty: public lookup (phone + invoice number) and admin claims workflow (T18)."""

from collections import defaultdict, deque
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.auth.models import User
from app.billing.models import Invoice
from app.core.db import get_session
from app.core.errors import AppError, ConflictError, NotFoundError
from app.inventory.lifecycle import transition
from app.inventory.models import Device, DeviceStatus
from app.warranty.models import Warranty, WarrantyClaim

public = APIRouter(prefix="/public/warranty", tags=["warranty"])
admin = APIRouter(prefix="/admin/warranty", tags=["warranty-admin"])
_perm = Depends(require_permission("warranty.manage"))


class RateLimited(AppError):
    status_code = 429
    code = "rate_limited"


_hits: dict[str, deque[float]] = defaultdict(deque)


def _rate_limit(request: Request, limit: int = 10, window: int = 600) -> None:
    now = datetime.now(UTC).timestamp()
    q = _hits[request.client.host if request.client else "?"]
    while q and q[0] < now - window:
        q.popleft()
    if len(q) >= limit:
        raise RateLimited("Too many lookups. Please try again in a few minutes.")
    q.append(now)


class LookupIn(BaseModel):
    phone: str = Field(min_length=10, max_length=15)
    invoice_number: str = Field(min_length=3, max_length=40)


def _today():
    return datetime.now(UTC).date()


@public.post("/lookup")
def lookup(body: LookupIn, request: Request, db: Session = Depends(get_session)) -> dict:
    """Needs both the phone and the invoice number. Response carries no PII and no IMEI."""
    _rate_limit(request)
    phone = body.phone.strip()[-10:]
    row = db.execute(
        select(Warranty, Invoice)
        .join(Invoice, Invoice.id == Warranty.invoice_id)
        .where(Invoice.number == body.invoice_number.strip(), Invoice.customer_phone == phone)
    ).first()
    if row is None:
        raise NotFoundError("No warranty found for these details")
    w, inv = row
    return {
        "invoice_number": inv.number,
        "device": inv.description.split(" (IMEI")[0],
        "starts_on": w.starts_on,
        "ends_on": w.ends_on,
        "months": w.months,
        "active": w.ends_on >= _today(),
    }


def _claim_out(c: WarrantyClaim) -> dict:
    return {
        "id": c.id,
        "warranty_id": c.warranty_id,
        "issue": c.issue,
        "status": c.status,
        "resolution_note": c.resolution_note,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


def _w_out(db: Session, w: Warranty, inv: Invoice) -> dict:
    claims = db.scalars(select(WarrantyClaim).where(WarrantyClaim.warranty_id == w.id))
    return {
        "id": w.id,
        "invoice_number": inv.number,
        "customer_name": inv.customer_name,
        "customer_phone": inv.customer_phone,
        "device": inv.description,
        "device_id": w.device_id,
        "starts_on": w.starts_on,
        "ends_on": w.ends_on,
        "active": w.ends_on >= _today(),
        "claims": [_claim_out(c) for c in claims],
    }


@admin.get("")
def list_warranties(
    q: str = "", user: User = _perm, db: Session = Depends(get_session)
) -> list[dict]:
    stmt = (
        select(Warranty, Invoice)
        .join(Invoice, Invoice.id == Warranty.invoice_id)
        .order_by(Warranty.id.desc())
        .limit(100)
    )
    q = q.strip()
    if q:
        stmt = stmt.where(Invoice.number.contains(q) | Invoice.customer_phone.contains(q))
    return [_w_out(db, w, i) for w, i in db.execute(stmt)]


class ClaimIn(BaseModel):
    issue: str = Field(min_length=3, max_length=2000)


@admin.post("/{wid}/claims", status_code=201)
def open_claim(
    wid: int, body: ClaimIn, user: User = _perm, db: Session = Depends(get_session)
) -> dict:
    w = db.get(Warranty, wid)
    if w is None:
        raise NotFoundError("Warranty not found")
    if w.ends_on < _today():
        raise ConflictError("This warranty has expired", code="warranty_expired")
    c = WarrantyClaim(warranty_id=wid, issue=body.issue.strip(), created_by=user.id)
    db.add(c)
    db.commit()
    return _claim_out(c)


FLOW = {
    "OPEN": {"IN_REVIEW", "APPROVED", "REJECTED"},
    "IN_REVIEW": {"APPROVED", "REJECTED"},
    "APPROVED": {"RESOLVED"},
    "REJECTED": set(),
    "RESOLVED": set(),
}


class ClaimPatch(BaseModel):
    status: str = Field(pattern="^(IN_REVIEW|APPROVED|REJECTED|RESOLVED)$")
    note: str = Field(default="", max_length=2000)


@admin.get("/claims")
def list_claims(
    status: str | None = None, user: User = _perm, db: Session = Depends(get_session)
) -> list[dict]:
    stmt = select(WarrantyClaim).order_by(WarrantyClaim.id.desc()).limit(100)
    if status:
        stmt = stmt.where(WarrantyClaim.status == status)
    return [_claim_out(c) for c in db.scalars(stmt)]


@admin.patch("/claims/{cid}")
def update_claim(
    cid: int, body: ClaimPatch, user: User = _perm, db: Session = Depends(get_session)
) -> dict:
    c = db.scalar(select(WarrantyClaim).where(WarrantyClaim.id == cid).with_for_update())
    if c is None:
        raise NotFoundError("Claim not found")
    if body.status not in FLOW[c.status]:
        raise ConflictError(
            f"Cannot move a claim from {c.status} to {body.status}", code="bad_claim_state"
        )
    w = db.get(Warranty, c.warranty_id)
    if body.status == "APPROVED":
        dev = db.get(Device, w.device_id)
        if dev.status == DeviceStatus.SOLD.value:  # take the unit back into the repair flow
            transition(db, dev.id, DeviceStatus.WARRANTY_HOLD, actor_user_id=user.id,
                       reason=f"warranty claim #{c.id}")  # fmt: skip
    if body.status == "RESOLVED":
        dev = db.get(Device, w.device_id)
        if dev.status == DeviceStatus.WARRANTY_HOLD.value:
            transition(db, dev.id, DeviceStatus.SOLD, actor_user_id=user.id,
                       reason=f"warranty claim #{c.id} resolved")  # fmt: skip
    c.status = body.status
    if body.note.strip():
        c.resolution_note = body.note.strip()
    db.commit()
    return _claim_out(c)
