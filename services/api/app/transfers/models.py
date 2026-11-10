"""Stock transfers warehouse <-> counter (T15).

REQUESTED -> (approve) IN_TRANSIT -> (receive) RECEIVED; REQUESTED -> REJECTED/CANCELLED.
Device status/location changes happen only through the lifecycle service.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import ID
from app.core.db import Base


class TransferStatus(enum.StrEnum):
    REQUESTED = "REQUESTED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class StockTransfer(Base):
    __tablename__ = "stock_transfers"
    __table_args__ = (
        CheckConstraint(
            "(from_counter_id IS NULL) != (to_counter_id IS NULL)", name="one_side_warehouse"
        ),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    # NULL counter id on a side = the warehouse.
    from_counter_id: Mapped[int | None] = mapped_column(ForeignKey("counters.id"), nullable=True)
    to_counter_id: Mapped[int | None] = mapped_column(ForeignKey("counters.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(12), default=TransferStatus.REQUESTED.value)
    note: Mapped[str] = mapped_column(Text, default="")
    requested_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    received_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StockTransferItem(Base):
    __tablename__ = "stock_transfer_items"
    __table_args__ = (UniqueConstraint("transfer_id", "device_id"),)
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    transfer_id: Mapped[int] = mapped_column(ForeignKey("stock_transfers.id"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    received: Mapped[int] = mapped_column(Integer, default=0)
