"""Online orders (T31). Customer contact/address are PII: never exposed publicly."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    number: Mapped[str] = mapped_column(String(16), unique=True)
    token: Mapped[str] = mapped_column(String(48), unique=True)
    checkout_id: Mapped[int] = mapped_column(ForeignKey("checkouts.id"), unique=True)
    email: Mapped[str] = mapped_column(String(160), index=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    address_line: Mapped[str] = mapped_column(String(300))
    city: Mapped[str] = mapped_column(String(80))
    pincode: Mapped[str] = mapped_column(String(6))
    total_paise: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(12), default="PLACED")
    carrier: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tracking_no: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    price_paise: Mapped[int] = mapped_column(Integer)


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    status: Mapped[str] = mapped_column(String(12))
    note: Mapped[str] = mapped_column(String(200), default="")
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReturnRequest(Base):
    """Return/refund for one order item (T32). One request per item."""

    __tablename__ = "return_requests"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"), unique=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    reason: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(10), default="REQUESTED")
    refund_paise: Mapped[int] = mapped_column(Integer, default=0)
    refund_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    admin_note: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
