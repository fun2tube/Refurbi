"""Commission statements and settlements (T19). Back-office + the counter's own statement.

Assumption (founder to confirm): the counter collects the customer's payment, so after
settlement it owes Refurbi `sales_total - commission`.
"""

from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.auth.models import User
from app.billing.models import Invoice
from app.commission.models import CommissionEntry, Settlement
from app.core.db import get_session
from app.core.errors import ConflictError, NotFoundError
from app.counters.models import Counter
from app.pos.models import Sale

admin = APIRouter(prefix="/admin/commissions", tags=["commission-admin"])
partner = APIRouter(prefix="/pos/counters/{counter_id}", tags=["commission"])
_manage = Depends(require_permission("counters.manage"))
_own = Depends(require_permission("commission.read", counter_param="counter_id"))


def _statement(db: Session, counter_id: int) -> dict:
    rows = db.execute(
        select(CommissionEntry, Invoice.number)
        .join(Sale, Sale.id == CommissionEntry.sale_id)
        .join(Invoice, Invoice.id == Sale.invoice_id)
        .where(CommissionEntry.counter_id == counter_id)
        .order_by(CommissionEntry.id.desc())
        .limit(500)
    ).all()
    acc = [e for e, _ in rows if e.status == "ACCRUED"]
    sales = sum(e.sale_price_paise for e in acc)
    comm = sum(e.amount_paise for e in acc)
    return {
        "counter_id": counter_id,
        "unsettled": {
            "units": len(acc),
            "sales_total_paise": sales,
            "commission_paise": comm,
            "net_due_to_refurbi_paise": sales - comm,
        },
        "entries": [
            {
                "invoice_number": n,
                "sale_price_paise": e.sale_price_paise,
                "commission_paise": e.amount_paise,
                "status": e.status,
                "settlement_id": e.settlement_id,
                "created_at": e.created_at,
            }
            for e, n in rows
        ],
    }


@admin.get("/counters/{counter_id}/statement")
def statement(counter_id: int, user: User = _manage, db: Session = Depends(get_session)) -> dict:
    if db.get(Counter, counter_id) is None:
        raise NotFoundError("Counter not found")
    return _statement(db, counter_id)


@admin.get("/summary")
def summary(user: User = _manage, db: Session = Depends(get_session)) -> list[dict]:
    rows = db.execute(
        select(
            Counter.id,
            Counter.name,
            func.count(CommissionEntry.id),
            func.coalesce(func.sum(CommissionEntry.amount_paise), 0),
        )
        .join(CommissionEntry, CommissionEntry.counter_id == Counter.id)
        .where(CommissionEntry.status == "ACCRUED")
        .group_by(Counter.id, Counter.name)
        .order_by(Counter.id)
    )
    return [
        {"counter_id": i, "counter": n, "unsettled_units": u, "unsettled_commission_paise": int(c)}
        for i, n, u, c in rows
    ]


class SettleIn(BaseModel):
    counter_id: int
    up_to: date | None = None  # default today (UTC); entries created on/before this date
    reference: str = Field(default="", max_length=80)


@admin.post("/settlements", status_code=201)
def settle(body: SettleIn, user: User = _manage, db: Session = Depends(get_session)) -> dict:
    up_to = body.up_to or datetime.now(UTC).date()
    entries = list(
        db.scalars(
            select(CommissionEntry)
            .where(
                CommissionEntry.counter_id == body.counter_id,
                CommissionEntry.status == "ACCRUED",
                func.date(CommissionEntry.created_at) <= up_to.isoformat(),
            )
            .with_for_update()
        )
    )
    if not entries:
        raise ConflictError("Nothing to settle for this counter", code="nothing_to_settle")
    s = Settlement(
        counter_id=body.counter_id,
        up_to=up_to,
        sales_total_paise=sum(e.sale_price_paise for e in entries),
        commission_paise=sum(e.amount_paise for e in entries),
        reference=body.reference.strip(),
        created_by=user.id,
    )
    db.add(s)
    db.flush()
    for e in entries:
        e.status, e.settlement_id = "SETTLED", s.id
    db.commit()
    return {
        "id": s.id,
        "counter_id": s.counter_id,
        "units": len(entries),
        "sales_total_paise": s.sales_total_paise,
        "commission_paise": s.commission_paise,
        "net_due_to_refurbi_paise": s.sales_total_paise - s.commission_paise,
    }


@partner.get("/commission")
def my_statement(counter_id: int, user: User = _own, db: Session = Depends(get_session)) -> dict:
    return _statement(db, counter_id)
