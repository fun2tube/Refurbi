"""Invoices and gap-free per-financial-year numbering (T16)."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base


class InvoiceSequence(Base):
    __tablename__ = "invoice_sequences"
    fy: Mapped[str] = mapped_column(String(8), primary_key=True)
    last_no: Mapped[int] = mapped_column(Integer, default=0)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("fy", "seq"),)
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    number: Mapped[str] = mapped_column(String(40), unique=True)
    fy: Mapped[str] = mapped_column(String(8))
    seq: Mapped[int] = mapped_column(Integer)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    counter_id: Mapped[int | None] = mapped_column(ForeignKey("counters.id"), nullable=True)
    mode: Mapped[str] = mapped_column(String(10))
    customer_name: Mapped[str] = mapped_column(String(120))
    customer_phone: Mapped[str] = mapped_column(String(20))
    customer_state_code: Mapped[str] = mapped_column(String(2))
    description: Mapped[str] = mapped_column(String(255))
    hsn_code: Mapped[str] = mapped_column(String(8))
    rate_bps: Mapped[int] = mapped_column(Integer)
    total_paise: Mapped[int] = mapped_column(BigInteger)
    taxable_paise: Mapped[int] = mapped_column(BigInteger)
    cgst_paise: Mapped[int] = mapped_column(BigInteger)
    sgst_paise: Mapped[int] = mapped_column(BigInteger)
    igst_paise: Mapped[int] = mapped_column(BigInteger)
    margin_paise: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    seller: Mapped[dict] = mapped_column(JSON)  # snapshot of seller details at issue time
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
