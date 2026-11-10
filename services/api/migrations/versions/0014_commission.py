"""commission

Revision ID: 0014
Revises: 0013
"""

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "commission_settlements",
        sa.Column("id", ID, nullable=False),
        sa.Column("counter_id", ID, sa.ForeignKey("counters.id"), nullable=False),
        sa.Column("up_to", sa.Date(), nullable=False),
        sa.Column("sales_total_paise", sa.BigInteger(), nullable=False),
        sa.Column("commission_paise", sa.BigInteger(), nullable=False),
        sa.Column("reference", sa.String(80), nullable=False),
        sa.Column("created_by", ID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_commission_settlements_counter_id", "commission_settlements", ["counter_id"]
    )
    op.create_table(
        "commission_entries",
        sa.Column("id", ID, nullable=False),
        sa.Column("sale_id", ID, sa.ForeignKey("sales.id"), nullable=False),
        sa.Column("counter_id", ID, sa.ForeignKey("counters.id"), nullable=False),
        sa.Column("sale_price_paise", sa.BigInteger(), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("settlement_id", ID, sa.ForeignKey("commission_settlements.id"), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sale_id"),
    )
    op.create_index("ix_commission_entries_counter_id", "commission_entries", ["counter_id"])


def downgrade() -> None:
    op.drop_table("commission_entries")
    op.drop_table("commission_settlements")
