"""Commission entries (one per sold device, amount frozen at sale time) and settlements (T19)."""

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base


class Settlement(Base):
    __tablename__ = "commission_settlements"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    counter_id: Mapped[int] = mapped_column(ForeignKey("counters.id"), index=True)
    up_to: Mapped[date] = mapped_column(Date)
    sales_total_paise: Mapped[int] = mapped_column(BigInteger)
    commission_paise: Mapped[int] = mapped_column(BigInteger)
    reference: Mapped[str] = mapped_column(String(80), default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommissionEntry(Base):
    __tablename__ = "commission_entries"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), unique=True)
    counter_id: Mapped[int] = mapped_column(ForeignKey("counters.id"), index=True)
    sale_price_paise: Mapped[int] = mapped_column(BigInteger)
    amount_paise: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(10), default="ACCRUED")  # ACCRUED | SETTLED
    settlement_id: Mapped[int | None] = mapped_column(
        ForeignKey("commission_settlements.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
