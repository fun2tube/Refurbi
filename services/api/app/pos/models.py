"""Counter sales (T17). Payment is recorded manually: cash / UPI QR / card. No gateway."""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base

PAYMENT_MODES = ("CASH", "UPI", "CARD")


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("payment_mode IN ('CASH','UPI','CARD')", name="payment_mode_valid"),
        CheckConstraint("price_paise >= 0", name="price_non_negative"),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), unique=True)
    counter_id: Mapped[int] = mapped_column(ForeignKey("counters.id"), index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), unique=True)
    sold_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    customer_phone: Mapped[str] = mapped_column(String(20))
    price_paise: Mapped[int] = mapped_column(BigInteger)
    payment_mode: Mapped[str] = mapped_column(String(8))
    payment_ref: Mapped[str] = mapped_column(
        String(60), default=""
    )  # UPI txn id / card last digits
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
