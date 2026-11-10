"""Online checkout holds (T29). Name/email/phone/address are customer PII: never public."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base


class Checkout(Base):
    __tablename__ = "checkouts"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    token: Mapped[str] = mapped_column(String(48), unique=True)  # unguessable public handle
    status: Mapped[str] = mapped_column(String(12), default="HOLD")  # HOLD|EXPIRED|CANCELLED|PAID
    customer_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(20))
    address_line: Mapped[str] = mapped_column(String(300))
    city: Mapped[str] = mapped_column(String(80))
    pincode: Mapped[str] = mapped_column(String(6))
    total_paise: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CheckoutItem(Base):
    __tablename__ = "checkout_items"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    checkout_id: Mapped[int] = mapped_column(ForeignKey("checkouts.id"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    price_paise: Mapped[int] = mapped_column(Integer)
