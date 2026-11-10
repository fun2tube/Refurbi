"""Stock ageing and exception alerts, computed on demand (no job table needed at this scale).

Kinds: AGEING_WARN (>=21d AVAILABLE), AGEING_CRITICAL (>=35d), QC_FAILED, TRANSIT_STUCK
(IN_TRANSIT > 3d), COUNTER_MISMATCH (device at a counter whose status is not a counter-valid
status, e.g. still in QC)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.catalog.models import ProductModel, ProductVariant
from app.inventory.models import Device, DeviceStatus, StockMovement

WARN_DAYS, CRITICAL_DAYS, TRANSIT_DAYS = 21, 35, 3
COUNTER_VALID = {"AVAILABLE", "RESERVED", "SOLD", "WARRANTY_HOLD", "RETURNED"}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def compute_alerts(db: Session, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(UTC)
    since = dict(
        db.execute(
            select(StockMovement.device_id, func.max(StockMovement.created_at))
            .where(StockMovement.to_status.in_(["AVAILABLE", "IN_TRANSIT"]))
            .group_by(StockMovement.device_id)
        ).all()
    )
    rows = db.execute(
        select(Device, ProductModel.name, ProductVariant.storage_gb)
        .join(ProductVariant, Device.variant_id == ProductVariant.id)
        .join(ProductModel, ProductVariant.model_id == ProductModel.id)
        .where(Device.status.notin_([DeviceStatus.SOLD.value, DeviceStatus.WRITTEN_OFF.value]))
    ).all()
    out: list[dict] = []

    def add(kind: str, severity: str, d: Device, name: str, gb: int, msg: str, days: int):
        out.append({"kind": kind, "severity": severity, "device_id": d.id,
                    "label": f"{name} {gb}GB (…{d.imei_last4})", "message": msg,
                    "days": days})  # fmt: skip

    for d, name, gb in rows:
        ref = _aware(since.get(d.id) or d.created_at)
        days = (now - ref).days
        if d.status == DeviceStatus.AVAILABLE.value:
            if days >= CRITICAL_DAYS:
                add("AGEING_CRITICAL", "critical", d, name, gb, f"In stock {days} days", days)
            elif days >= WARN_DAYS:
                add("AGEING_WARN", "warning", d, name, gb, f"In stock {days} days", days)
        if d.status == DeviceStatus.QC_FAILED.value:
            add("QC_FAILED", "warning", d, name, gb, "QC failed; needs repair or write-off", days)
        if d.status == DeviceStatus.IN_TRANSIT.value and now - ref > timedelta(days=TRANSIT_DAYS):
            add("TRANSIT_STUCK", "critical", d, name, gb, f"In transit for {days} days", days)
        if d.location_kind == "COUNTER" and d.status not in COUNTER_VALID:
            add("COUNTER_MISMATCH", "warning", d, name, gb,
                f"Status {d.status} but located at a counter", days)  # fmt: skip
    order = {"critical": 0, "warning": 1}
    out.sort(key=lambda a: (order[a["severity"]], -a["days"]))
    return out
