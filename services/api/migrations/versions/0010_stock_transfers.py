"""stock_transfers

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "stock_transfers",
        sa.Column("id", ID, nullable=False),
        sa.Column("from_counter_id", ID, sa.ForeignKey("counters.id"), nullable=True),
        sa.Column("to_counter_id", ID, sa.ForeignKey("counters.id"), nullable=True),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("requested_by", ID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_by", ID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("received_by", ID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(from_counter_id IS NULL) != (to_counter_id IS NULL)", name="ck_stock_transfers_one_side_warehouse"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "stock_transfer_items",
        sa.Column("id", ID, nullable=False),
        sa.Column("transfer_id", ID, sa.ForeignKey("stock_transfers.id"), nullable=False),
        sa.Column("device_id", ID, sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("received", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transfer_id", "device_id"),
    )
    op.create_index("ix_stock_transfer_items_transfer_id", "stock_transfer_items", ["transfer_id"])
    op.create_index("ix_stock_transfer_items_device_id", "stock_transfer_items", ["device_id"])


def downgrade() -> None:
    op.drop_table("stock_transfer_items")
    op.drop_table("stock_transfers")
