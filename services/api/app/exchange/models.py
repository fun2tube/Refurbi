"""Exchange enquiry leads (T26). Customer PII: admin-only, never in public responses."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base


class ExchangeLead(Base):
    __tablename__ = "exchange_leads"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    brand: Mapped[str] = mapped_column(String(60))
    model_name: Mapped[str] = mapped_column(String(120))
    storage_gb: Mapped[int] = mapped_column(Integer)
    age_band: Mapped[str] = mapped_column(String(12))
    screen: Mapped[str] = mapped_column(String(12))
    body: Mapped[str] = mapped_column(String(12))
    battery: Mapped[str] = mapped_column(String(12))
    has_accessories: Mapped[bool] = mapped_column(Boolean, default=True)
    powers_on: Mapped[bool] = mapped_column(Boolean, default=True)
    quote_low_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quote_high_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    contact: Mapped[str] = mapped_column(String(160))  # phone or email, PII
    city: Mapped[str] = mapped_column(String(80), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="NEW")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
