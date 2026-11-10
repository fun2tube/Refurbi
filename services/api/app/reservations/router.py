from collections import defaultdict, deque
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.core.db import get_session
from app.core.errors import AppError
from app.core.settings import get_settings
from app.reservations import service
from app.reservations.email import EmailSender, FakeEmailSender, get_email_sender
from app.reservations.models import Reservation

public = APIRouter(prefix="/public/reservations", tags=["reservations"])
admin = APIRouter(prefix="/admin/reservations", tags=["reservations-admin"])
_perm = Depends(require_permission("leads.manage"))


Email = Annotated[str, StringConstraints(max_length=160, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


class RateLimited(AppError):
    status_code = 429
    code = "rate_limited"


_hits: dict[str, deque[float]] = defaultdict(deque)


def _rate_limit(key: str, limit: int, window: int = 600) -> None:
    now = datetime.now(UTC).timestamp()
    q = _hits[key]
    while q and q[0] < now - window:
        q.popleft()
    if len(q) >= limit:
        raise RateLimited("Too many requests. Please try again in a few minutes.")
    q.append(now)


class OtpIn(BaseModel):
    email: Email


class ReserveIn(BaseModel):
    unit_id: int
    name: str = Field(min_length=1, max_length=120)
    email: Email
    otp: str = Field(min_length=4, max_length=8)


class ReservedOut(BaseModel):
    code: str
    expires_at: datetime
    store_name: str | None
    store_city: str | None
    pay_at_store: bool = True


@public.post("/otp", status_code=202)
def request_otp(
    body: OtpIn,
    request: Request,
    db: Session = Depends(get_session),
    sender: EmailSender = Depends(get_email_sender),
):
    ip = request.client.host if request.client else "?"
    _rate_limit(f"ip:{ip}", 10)
    _rate_limit(f"em:{body.email.lower()}", 3)
    code = service.send_otp(db, body.email, sender)
    out: dict = {"sent": True}  # uniform response; reveals nothing about the address
    # Demo only: with the fake email adapter outside production, show the code so the preview
    # can be tried without an email account. Never happens once a Brevo key is configured.
    if isinstance(sender, FakeEmailSender) and get_settings().app_env in ("dev", "preview", "test"):
        out["demo_code"] = code
    return out


@public.post("", response_model=ReservedOut, status_code=201)
def create_reservation(
    body: ReserveIn,
    request: Request,
    db: Session = Depends(get_session),
    sender: EmailSender = Depends(get_email_sender),
):
    _rate_limit(f"rs:{request.client.host if request.client else '?'}", 10)
    r, counter = service.reserve(db, body.unit_id, body.name, body.email, body.otp, sender)
    return ReservedOut(
        code=r.code,
        expires_at=r.expires_at,
        store_name=counter.name if counter else None,
        store_city=counter.city if counter else None,
    )


class AdminReservation(BaseModel):
    id: int
    code: str
    device_id: int
    counter_id: int | None
    customer_name: str
    email: str
    status: str
    expires_at: datetime


@admin.get("", response_model=list[AdminReservation], dependencies=[_perm])
def list_reservations(status: str | None = None, db: Session = Depends(get_session)):
    stmt = select(Reservation).order_by(Reservation.id.desc()).limit(200)
    if status:
        stmt = stmt.where(Reservation.status == status.upper())
    return [AdminReservation.model_validate(r, from_attributes=True) for r in db.scalars(stmt)]


@admin.post("/expire", dependencies=[_perm])
def expire_now(db: Session = Depends(get_session)):
    return {"released": service.release_expired(db)}


@admin.post("/{reservation_id}/cancel", response_model=AdminReservation)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_session),
    user=Depends(require_permission("leads.manage")),
):
    r = service.cancel(db, reservation_id, getattr(user, "id", None))
    return AdminReservation.model_validate(r, from_attributes=True)
