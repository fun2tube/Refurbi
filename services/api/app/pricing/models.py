from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base


class PricingRule(Base):
    """Target gross margin (basis points of landed cost) per grade. Missing grade -> defaults."""

    __tablename__ = "pricing_rules"
    __table_args__ = (CheckConstraint("target_margin_bps BETWEEN 0 AND 10000", name="bps_range"),)
    grade: Mapped[str] = mapped_column(String(1), primary_key=True)
    target_margin_bps: Mapped[int] = mapped_column(Integer)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DeviceCost(Base):
    """Extra landed-cost entries (repair, logistics) on top of devices.cost_paise (purchase)."""

    __tablename__ = "device_costs"
    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="amount_positive"),
        CheckConstraint("kind IN ('REPAIR', 'LOGISTICS')", name="kind_valid"),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    kind: Mapped[str] = mapped_column(String(12))
    amount_paise: Mapped[int] = mapped_column(BigInteger)
    note: Mapped[str] = mapped_column(String(255), default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
