"""Warranty (auto-created per sale) and claims (T18)."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base

CLAIM_STATUSES = ("OPEN", "IN_REVIEW", "APPROVED", "REJECTED", "RESOLVED")


class Warranty(Base):
    __tablename__ = "warranties"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    sale_id: Mapped[int | None] = mapped_column(ForeignKey("sales.id"), unique=True, nullable=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), unique=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    months: Mapped[int] = mapped_column()
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WarrantyClaim(Base):
    __tablename__ = "warranty_claims"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    warranty_id: Mapped[int] = mapped_column(ForeignKey("warranties.id"), index=True)
    issue: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12), default="OPEN")
    resolution_note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
