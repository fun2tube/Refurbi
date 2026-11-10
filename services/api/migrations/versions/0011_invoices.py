"""invoices

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "invoice_sequences",
        sa.Column("fy", sa.String(8), nullable=False),
        sa.Column("last_no", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("fy"),
    )
    op.create_table(
        "invoices",
        sa.Column("id", ID, nullable=False),
        sa.Column("number", sa.String(40), nullable=False),
        sa.Column("fy", sa.String(8), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("device_id", ID, sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("counter_id", ID, sa.ForeignKey("counters.id"), nullable=True),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("customer_name", sa.String(120), nullable=False),
        sa.Column("customer_phone", sa.String(20), nullable=False),
        sa.Column("customer_state_code", sa.String(2), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("hsn_code", sa.String(8), nullable=False),
        sa.Column("rate_bps", sa.Integer(), nullable=False),
        sa.Column("total_paise", sa.BigInteger(), nullable=False),
        sa.Column("taxable_paise", sa.BigInteger(), nullable=False),
        sa.Column("cgst_paise", sa.BigInteger(), nullable=False),
        sa.Column("sgst_paise", sa.BigInteger(), nullable=False),
        sa.Column("igst_paise", sa.BigInteger(), nullable=False),
        sa.Column("margin_paise", sa.BigInteger(), nullable=True),
        sa.Column("seller", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("number"),
        sa.UniqueConstraint("fy", "seq"),
    )
    op.create_index("ix_invoices_device_id", "invoices", ["device_id"])


def downgrade() -> None:
    op.drop_table("invoices")
    op.drop_table("invoice_sequences")
