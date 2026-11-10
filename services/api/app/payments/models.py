from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    checkout_id: Mapped[int] = mapped_column(ForeignKey("checkouts.id"), index=True)
    gateway: Mapped[str] = mapped_column(String(12))  # fake | razorpay
    gateway_order_id: Mapped[str] = mapped_column(String(64), unique=True)
    gateway_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount_paise: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(12), default="CREATED"
    )  # CREATED|PAID|FAILED|REFUND_DUE
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PaymentEvent(Base):
    """Every webhook event is recorded once; the unique event_id makes processing idempotent."""

    __tablename__ = "payment_events"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(80), unique=True)
    event_type: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
