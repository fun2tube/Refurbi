"""Device-level inventory. One row in `devices` = one physical handset (D5).

Status changes must go through the lifecycle service (T08); this module is schema only.
Sensitive columns (imei_*, cost_paise, supplier) are never exposed by public schemas.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.models import ID
from app.core.db import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


class DeviceStatus(enum.StrEnum):
    PURCHASED = "PURCHASED"
    IMEI_CHECKED = "IMEI_CHECKED"
    QC_PENDING = "QC_PENDING"
    QC_PASSED = "QC_PASSED"
    QC_FAILED = "QC_FAILED"
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    IN_TRANSIT = "IN_TRANSIT"
    RETURNED = "RETURNED"
    WARRANTY_HOLD = "WARRANTY_HOLD"
    REPAIR = "REPAIR"
    BLACKLISTED = "BLACKLISTED"
    WRITTEN_OFF = "WRITTEN_OFF"


class Grade(enum.StrEnum):
    """Placeholder grades pending founder grade definitions."""

    A = "A"
    B = "B"
    C = "C"


class LocationKind(enum.StrEnum):
    WAREHOUSE = "WAREHOUSE"
    COUNTER = "COUNTER"
    IN_TRANSIT = "IN_TRANSIT"


def _in(col: str, enum_cls: type[enum.StrEnum]) -> str:
    return f"{col} IN ({', '.join(repr(e.value) for e in enum_cls)})"


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (
        CheckConstraint(_in("status", DeviceStatus), name="status_valid"),
        CheckConstraint("grade IS NULL OR " + _in("grade", Grade), name="grade_valid"),
        CheckConstraint(_in("location_kind", LocationKind), name="location_kind_valid"),
        CheckConstraint(
            "battery_health IS NULL OR (battery_health BETWEEN 0 AND 100)",
            name="battery_range",
        ),
        CheckConstraint("cost_paise >= 0", name="cost_non_negative"),
        CheckConstraint("price_paise IS NULL OR price_paise >= 0", name="price_non_negative"),
        CheckConstraint(
            "(location_kind = 'COUNTER') = (counter_id IS NOT NULL)", name="counter_iff_counter"
        ),
        Index("ix_devices_status_location", "status", "location_kind", "counter_id"),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), index=True)
    imei_encrypted: Mapped[str] = mapped_column(Text)
    imei_hash: Mapped[str] = mapped_column(String(64), unique=True)
    imei_last4: Mapped[str] = mapped_column(String(4))  # staff search aid; never public
    grade: Mapped[str | None] = mapped_column(String(1), nullable=True)
    battery_health: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_paise: Mapped[int] = mapped_column(BigInteger, default=0)
    price_paise: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=DeviceStatus.PURCHASED.value)
    location_kind: Mapped[str] = mapped_column(String(20), default=LocationKind.WAREHOUSE.value)
    # No FK until the counters table exists (T14).
    counter_id: Mapped[int | None] = mapped_column(ID, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tests: Mapped[list["DeviceTest"]] = relationship(back_populates="device")
    photos: Mapped[list["DevicePhoto"]] = relationship(
        order_by="DevicePhoto.sort_order, DevicePhoto.id"
    )


class DeviceTest(Base):
    """QC checklist result (JSONB). At most one `is_current` row per device (partial unique)."""

    __tablename__ = "device_tests"
    __table_args__ = (
        Index(
            "uq_device_tests_current",
            "device_id",
            unique=True,
            postgresql_where=text("is_current"),
            sqlite_where=text("is_current"),
        ),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    checklist: Mapped[dict] = mapped_column(JSONType, default=dict)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    tested_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    tested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    device: Mapped[Device] = relationship(back_populates="tests")


class DevicePhoto(Base):
    __tablename__ = "device_photos"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    kind: Mapped[str] = mapped_column(String(30), default="cosmetic")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class StockMovement(Base):
    """Append-only ledger of every status/location change (written by the lifecycle service)."""

    __tablename__ = "stock_movements"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20))
    from_location: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_location: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reason: Mapped[str] = mapped_column(String(255), default="")
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_entity", "entity_type", "entity_id"),)
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column(ID)
    action: Mapped[str] = mapped_column(String(50))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    before: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
