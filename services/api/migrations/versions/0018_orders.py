"""orders, items, status history

Revision ID: 0018
Revises: 0017
"""

import sqlalchemy as sa
from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
NOW = sa.func.now()


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", ID, nullable=False),
        sa.Column("number", sa.String(16), nullable=False),
        sa.Column("token", sa.String(48), nullable=False),
        sa.Column("checkout_id", ID, sa.ForeignKey("checkouts.id"), nullable=False),
        sa.Column("email", sa.String(160), nullable=False),
        sa.Column("customer_name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("address_line", sa.String(300), nullable=False),
        sa.Column("city", sa.String(80), nullable=False),
        sa.Column("pincode", sa.String(6), nullable=False),
        sa.Column("total_paise", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("carrier", sa.String(40), nullable=True),
        sa.Column("tracking_no", sa.String(60), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_orders")),
        sa.UniqueConstraint("number", name=op.f("uq_orders_number")),
        sa.UniqueConstraint("token", name=op.f("uq_orders_token")),
        sa.UniqueConstraint("checkout_id", name=op.f("uq_orders_checkout_id")),
    )
    op.create_index(op.f("ix_orders_email"), "orders", ["email"])
    op.create_table(
        "order_items",
        sa.Column("id", ID, nullable=False),
        sa.Column("order_id", ID, sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("device_id", ID, sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("price_paise", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_items")),
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"])
    op.create_index(op.f("ix_order_items_device_id"), "order_items", ["device_id"])
    op.create_table(
        "order_status_history",
        sa.Column("id", ID, nullable=False),
        sa.Column("order_id", ID, sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("note", sa.String(200), nullable=False),
        sa.Column("actor_user_id", ID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_status_history")),
    )
    op.create_index(op.f("ix_order_status_history_order_id"), "order_status_history", ["order_id"])


def downgrade() -> None:
    op.drop_table("order_status_history")
    op.drop_table("order_items")
    op.drop_table("orders")
