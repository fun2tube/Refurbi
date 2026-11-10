"""Counters (retail partner locations), agreements and commission rules (T14).

A counter is publicly visible (store pages, its stock) only when `is_verified` and `is_active`.
Agreement and commission data are back-office only.
"""

import enum
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base


class Counter(Base):
    __tablename__ = "counters"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(80), default="")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    address: Mapped[str] = mapped_column(Text, default="")
    owner_name: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommissionType(enum.StrEnum):
    FLAT = "FLAT"  # value = paise per device
    PERCENT = "PERCENT"  # value = basis points of the sale price


class CounterAgreement(Base):
    __tablename__ = "counter_agreements"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    counter_id: Mapped[int] = mapped_column(ForeignKey("counters.id"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_ref: Mapped[str] = mapped_column(String(200), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommissionRule(Base):
    """Per-counter commission. `model_id` NULL = default for the counter; a model-specific rule
    wins over the default. Money in paise, percentages in basis points."""

    __tablename__ = "commission_rules"
    __table_args__ = (
        CheckConstraint("kind IN ('FLAT', 'PERCENT')", name="kind_valid"),
        CheckConstraint("value >= 0", name="value_non_negative"),
        CheckConstraint("kind <> 'PERCENT' OR value <= 10000", name="percent_max"),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    counter_id: Mapped[int] = mapped_column(ForeignKey("counters.id"), index=True)
    model_id: Mapped[int | None] = mapped_column(ForeignKey("product_models.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(10))
    value: Mapped[int] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def commission_for(rules: list["CommissionRule"], model_id: int, price_paise: int) -> int:
    """Commission in paise: model-specific active rule, else counter default, else 0."""
    active = [r for r in rules if r.is_active]
    rule = next((r for r in active if r.model_id == model_id), None) or next(
        (r for r in active if r.model_id is None), None
    )
    if rule is None:
        return 0
    return rule.value if rule.kind == "FLAT" else price_paise * rule.value // 10_000
