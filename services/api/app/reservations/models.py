"""Store-pickup reservations (T24) and email OTPs. Email is customer PII: never public."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base


class EmailOtp(Base):
    __tablename__ = "email_otps"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    email: Mapped[str] = mapped_column(String(160), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    used: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Reservation(Base):
    __tablename__ = "reservations"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    code: Mapped[str] = mapped_column(String(12), unique=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    counter_id: Mapped[int | None] = mapped_column(ID, nullable=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160))  # PII
    status: Mapped[str] = mapped_column(
        String(12), default="ACTIVE"
    )  # ACTIVE|EXPIRED|CANCELLED|COLLECTED
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
