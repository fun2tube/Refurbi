"""Suppliers, purchase orders, goods receipts and IMEI-check records (T09).

Supplier data and costs are back-office only; nothing here is served publicly.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.models import ID
from app.core.db import Base


class POStatus(enum.StrEnum):
    DRAFT = "DRAFT"
    ORDERED = "ORDERED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class ImeiResult(enum.StrEnum):
    CLEAR = "CLEAR"
    BLOCKED = "BLOCKED"


class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    contact_name: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    city: Mapped[str] = mapped_column(String(80), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default=POStatus.DRAFT.value)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    supplier: Mapped[Supplier] = relationship()
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        back_populates="po", order_by="PurchaseOrderLine.id"
    )


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="qty_positive"),
        CheckConstraint("unit_cost_paise >= 0", name="cost_non_negative"),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    po_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_cost_paise: Mapped[int] = mapped_column(BigInteger)

    po: Mapped[PurchaseOrder] = relationship(back_populates="lines")


class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    po_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), index=True)
    received_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    items: Mapped[list["GoodsReceiptItem"]] = relationship(back_populates="receipt")


class GoodsReceiptItem(Base):
    __tablename__ = "goods_receipt_items"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("goods_receipts.id"), index=True)
    line_id: Mapped[int] = mapped_column(ForeignKey("purchase_order_lines.id"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), unique=True)

    receipt: Mapped[GoodsReceipt] = relationship(back_populates="items")


class ImeiCheck(Base):
    """Result of an IMEI blacklist/CEIR lookup, one row per check (history kept)."""

    __tablename__ = "imei_checks"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    result: Mapped[str] = mapped_column(String(10))
    provider: Mapped[str] = mapped_column(String(30))
    checked_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
