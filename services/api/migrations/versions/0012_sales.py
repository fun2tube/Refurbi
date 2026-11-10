"""sales

Revision ID: 0012
Revises: 0011
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "sales",
        sa.Column("id", ID, nullable=False),
        sa.Column("device_id", ID, sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("counter_id", ID, sa.ForeignKey("counters.id"), nullable=False),
        sa.Column("invoice_id", ID, sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("sold_by", ID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("customer_name", sa.String(120), nullable=False),
        sa.Column("customer_phone", sa.String(20), nullable=False),
        sa.Column("price_paise", sa.BigInteger(), nullable=False),
        sa.Column("payment_mode", sa.String(8), nullable=False),
        sa.Column("payment_ref", sa.String(60), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "payment_mode IN ('CASH','UPI','CARD')", name="ck_sales_payment_mode_valid"
        ),
        sa.CheckConstraint("price_paise >= 0", name="ck_sales_price_non_negative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id"),
        sa.UniqueConstraint("invoice_id"),
    )
    op.create_index("ix_sales_counter_id", "sales", ["counter_id"])


def downgrade() -> None:
    op.drop_table("sales")
