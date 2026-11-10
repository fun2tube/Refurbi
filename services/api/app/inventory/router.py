"""Back-office inventory views (T12). IMEI is never returned in full: only the last 4 digits."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.auth.models import User
from app.catalog.models import Brand, ProductModel, ProductVariant
from app.core.db import get_session
from app.core.errors import NotFoundError
from app.core.pagination import PageDep, make_page
from app.counters.models import Counter
from app.inventory.alerts import compute_alerts
from app.inventory.models import Device, DevicePhoto, DeviceTest, StockMovement

router = APIRouter(prefix="/admin/inventory", tags=["inventory-admin"])
_perm = Depends(require_permission("inventory.read"))


def _row(d: Device, v: ProductVariant, m: ProductModel, b: Brand, counter: str | None) -> dict:
    age = (datetime.now(UTC) - d.created_at.replace(tzinfo=d.created_at.tzinfo or UTC)).days
    return {
        "id": d.id,
        "brand": b.name,
        "model": m.name,
        "storage_gb": v.storage_gb,
        "color": v.color,
        "imei_last4": d.imei_last4,
        "grade": d.grade,
        "battery_health": d.battery_health,
        "status": d.status,
        "location_kind": d.location_kind,
        "counter_id": d.counter_id,
        "location": counter or d.location_kind.title(),
        "price_paise": d.price_paise,
        "cost_paise": d.cost_paise,
        "age_days": age,
    }


@router.get("/devices")
def list_devices(
    params: PageDep,
    brand: str | None = None,
    model: str | None = None,
    status: str | None = None,
    grade: str | None = None,
    min_battery: int | None = None,
    location_kind: str | None = None,
    counter_id: int | None = None,
    min_age_days: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_session),
    _: User = _perm,
):
    stmt = (
        select(Device, ProductVariant, ProductModel, Brand, Counter.name)
        .join(ProductVariant, Device.variant_id == ProductVariant.id)
        .join(ProductModel, ProductVariant.model_id == ProductModel.id)
        .join(Brand, ProductModel.brand_id == Brand.id)
        .outerjoin(Counter, Device.counter_id == Counter.id)
        .order_by(Device.id.desc())
    )
    if brand:
        stmt = stmt.where(Brand.slug == brand)
    if model:
        stmt = stmt.where(ProductModel.name.ilike(f"%{model}%"))
    if status:
        stmt = stmt.where(Device.status == status)
    if grade:
        stmt = stmt.where(Device.grade == grade)
    if min_battery is not None:
        stmt = stmt.where(Device.battery_health >= min_battery)
    if location_kind:
        stmt = stmt.where(Device.location_kind == location_kind)
    if counter_id:
        stmt = stmt.where(Device.counter_id == counter_id)
    if min_age_days:
        stmt = stmt.where(Device.created_at <= datetime.now(UTC) - timedelta(days=min_age_days))
    if q:
        stmt = stmt.where(Device.imei_last4 == q.strip()[-4:] if q.strip().isdigit() else False)
    rows = db.execute(stmt.limit(params.page_size).offset(params.offset)).all()
    total = len(db.execute(stmt.with_only_columns(Device.id).order_by(None)).all())
    return make_page([_row(*r) for r in rows], total, params)


@router.get("/devices/{device_id}")
def device_detail(device_id: int, db: Session = Depends(get_session), _: User = _perm):
    d = db.get(Device, device_id)
    if d is None:
        raise NotFoundError("Device not found")
    v = db.get(ProductVariant, d.variant_id)
    m = db.get(ProductModel, v.model_id)
    counter = db.get(Counter, d.counter_id).name if d.counter_id else None
    moves = db.scalars(
        select(StockMovement).where(StockMovement.device_id == d.id).order_by(StockMovement.id)
    ).all()
    tests = db.scalars(
        select(DeviceTest).where(DeviceTest.device_id == d.id).order_by(DeviceTest.id.desc())
    ).all()
    photos = db.scalars(select(DevicePhoto).where(DevicePhoto.device_id == d.id)).all()
    return {
        **_row(d, v, m, m.brand, counter),
        "timeline": [
            {
                "at": x.created_at,
                "from": x.from_status,
                "to": x.to_status,
                "from_location": x.from_location,
                "to_location": x.to_location,
                "reason": x.reason,
            }
            for x in moves
        ],
        "tests": [
            {
                "at": t.tested_at,
                "passed": t.passed,
                "is_current": t.is_current,
                "results": t.checklist.get("results", {}),
                "notes": t.checklist.get("notes", ""),
            }
            for t in tests
        ],
        "photos": [{"id": p.id, "url": p.url, "kind": p.kind} for p in photos],
    }


@router.get("/alerts")
def alerts(db: Session = Depends(get_session), _: User = _perm):
    items = compute_alerts(db)
    counts: dict[str, int] = {}
    for a in items:
        counts[a["kind"]] = counts.get(a["kind"], 0) + 1
    return {"counts": counts, "total": len(items), "items": items[:200]}
