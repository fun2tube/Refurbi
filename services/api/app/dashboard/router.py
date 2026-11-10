"""Admin dashboard (T20). Staff only (reports.read via inventory.read); aggregates, no IMEI/PII."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.auth.models import User
from app.core.db import get_session
from app.counters.models import Counter
from app.inventory.models import Device
from app.pos.models import Sale

router = APIRouter(prefix="/admin/dashboard", tags=["dashboard-admin"])
IST = timedelta(hours=5, minutes=30)
SELLABLE = ("AVAILABLE", "RESERVED")
BUCKETS = [("0-7", 0, 7), ("8-20", 8, 20), ("21-34", 21, 34), ("35+", 35, 10**6)]


def _today_start_utc(now: datetime) -> datetime:
    local = now + IST  # "today" is the Indian calendar day
    return local.replace(hour=0, minute=0, second=0, microsecond=0) - IST


def build_dashboard(db: Session, now: datetime) -> dict:
    start = _today_start_utc(now)
    month_start = (start + IST).replace(day=1) - IST

    def sales_agg(since: datetime):
        row = db.execute(
            select(
                func.count(Sale.id),
                func.coalesce(func.sum(Sale.price_paise), 0),
                func.coalesce(func.sum(Device.cost_paise), 0),
            )
            .join(Device, Device.id == Sale.device_id)
            .where(Sale.created_at >= since)
        ).one()
        units, revenue, cost = int(row[0]), int(row[1]), int(row[2])
        return {
            "units": units,
            "sales_paise": revenue,
            "gross_margin_paise": revenue - cost,
        }

    stock_rows = db.execute(
        select(Device.location_kind, Counter.name, func.count(Device.id), Device.counter_id)
        .outerjoin(Counter, Counter.id == Device.counter_id)
        .where(Device.status.in_(SELLABLE))
        .group_by(Device.location_kind, Counter.name, Device.counter_id)
        .order_by(Device.location_kind, Counter.name)
    ).all()
    stock = [
        {"location": name or kind.title(), "counter_id": cid, "units": int(n)}
        for kind, name, n, cid in stock_rows
    ]

    ages = [
        (now - (c if c.tzinfo else c.replace(tzinfo=UTC))).days
        for (c,) in db.execute(select(Device.created_at).where(Device.status.in_(SELLABLE)))
    ]
    ageing = [
        {"bucket": label, "units": sum(1 for a in ages if lo <= a <= hi)}
        for label, lo, hi in BUCKETS
    ]

    board = db.execute(
        select(Counter.id, Counter.name, func.count(Sale.id), func.sum(Sale.price_paise))
        .join(Sale, Sale.counter_id == Counter.id)
        .where(Sale.created_at >= month_start)
        .group_by(Counter.id, Counter.name)
        .order_by(func.sum(Sale.price_paise).desc())
        .limit(10)
    ).all()
    return {
        "generated_at": now.isoformat(),
        "today": sales_agg(start),
        "month": sales_agg(month_start),
        "stock_by_location": stock,
        "ageing": ageing,
        "counter_leaderboard": [
            {"counter_id": i, "counter": n, "units": int(u), "sales_paise": int(s)}
            for i, n, u, s in board
        ],
    }


@router.get("")
def dashboard(
    db: Session = Depends(get_session), _: User = Depends(require_permission("inventory.read"))
):
    return build_dashboard(db, datetime.now(UTC))
