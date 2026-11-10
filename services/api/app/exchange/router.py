from collections import defaultdict, deque
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.core.db import get_session
from app.core.errors import AppError, NotFoundError
from app.exchange.models import ExchangeLead
from app.exchange.rules import estimate

public = APIRouter(prefix="/public/exchange", tags=["exchange"])
admin = APIRouter(prefix="/admin/exchange", tags=["exchange-admin"])
_perm = Depends(require_permission("leads.manage"))


class RateLimited(AppError):
    status_code = 429
    code = "rate_limited"


_hits: dict[str, deque[float]] = defaultdict(deque)


def _rate_limit(request: Request, limit: int = 10, window: int = 600) -> None:
    """Tiny per-IP in-memory limiter (best effort; T34 replaces with a shared limiter)."""
    now = datetime.now(UTC).timestamp()
    q = _hits[request.client.host if request.client else "?"]
    while q and q[0] < now - window:
        q.popleft()
    if len(q) >= limit:
        raise RateLimited("Too many requests. Please try again in a few minutes.")
    q.append(now)


class Answers(BaseModel):
    brand: str = Field(min_length=1, max_length=60)
    model_name: str = Field(min_length=1, max_length=120)
    storage_gb: Literal[64, 128, 256, 512]
    age_band: Literal["under_1", "1_2", "2_3", "3_4", "over_4"]
    screen: Literal["perfect", "scratches", "cracked"]
    body: Literal["perfect", "dents", "damaged"]
    battery: Literal["good", "fair", "poor"]
    has_accessories: bool = True
    powers_on: bool = True


class QuoteOut(BaseModel):
    low_paise: int | None
    high_paise: int | None
    needs_inspection: bool
    is_demo_estimate: bool = True
    disclaimer: str = (
        "Indicative range only. The final offer is confirmed after an in-store inspection. "
        "Demo estimate until real exchange rates are set."
    )


class LeadIn(Answers):
    customer_name: str = Field(min_length=1, max_length=120)
    contact: str = Field(min_length=5, max_length=160)
    city: str = Field(default="", max_length=80)
    notes: str = Field(default="", max_length=1000)


def _quote(a: Answers) -> QuoteOut:
    q = estimate(
        **a.model_dump(
            include={
                "age_band",
                "storage_gb",
                "screen",
                "body",
                "battery",
                "has_accessories",
                "powers_on",
            }
        )
    )
    if q is None:
        return QuoteOut(low_paise=None, high_paise=None, needs_inspection=True)
    return QuoteOut(low_paise=q.low_paise, high_paise=q.high_paise, needs_inspection=False)


@public.post("/quote", response_model=QuoteOut)
def quote(a: Answers, request: Request) -> QuoteOut:
    _rate_limit(request, limit=30)
    return _quote(a)


@public.post("/leads", response_model=QuoteOut, status_code=201)
def create_lead(body: LeadIn, request: Request, db: Session = Depends(get_session)) -> QuoteOut:
    """Save an enquiry. The response carries only the quote - never lead data."""
    _rate_limit(request)
    q = _quote(body)
    db.add(
        ExchangeLead(
            **body.model_dump(),
            quote_low_paise=q.low_paise,
            quote_high_paise=q.high_paise,
        )
    )
    db.commit()
    return q


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    brand: str
    model_name: str
    storage_gb: int
    age_band: str
    screen: str
    body: str
    battery: str
    has_accessories: bool
    powers_on: bool
    quote_low_paise: int | None
    quote_high_paise: int | None
    customer_name: str
    contact: str
    city: str
    notes: str
    status: str
    created_at: datetime


class StatusIn(BaseModel):
    status: Literal["NEW", "CONTACTED", "WON", "LOST"]


@admin.get("/leads", response_model=list[LeadOut], dependencies=[_perm])
def list_leads(status: str | None = None, db: Session = Depends(get_session)):
    stmt = select(ExchangeLead).order_by(ExchangeLead.id.desc()).limit(200)
    if status:
        stmt = stmt.where(ExchangeLead.status == status)
    return db.scalars(stmt).all()


@admin.patch("/leads/{lead_id}", response_model=LeadOut, dependencies=[_perm])
def set_status(lead_id: int, body: StatusIn, db: Session = Depends(get_session)):
    lead = db.get(ExchangeLead, lead_id)
    if not lead:
        raise NotFoundError("Lead not found")
    lead.status = body.status
    db.commit()
    return lead
