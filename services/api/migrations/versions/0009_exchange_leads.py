"""exchange_leads

Revision ID: 0009
Revises: 0008
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "exchange_leads",
        sa.Column("id", ID, nullable=False),
        sa.Column("brand", sa.String(60), nullable=False),
        sa.Column("model_name", sa.String(120), nullable=False),
        sa.Column("storage_gb", sa.Integer(), nullable=False),
        sa.Column("age_band", sa.String(12), nullable=False),
        sa.Column("screen", sa.String(12), nullable=False),
        sa.Column("body", sa.String(12), nullable=False),
        sa.Column("battery", sa.String(12), nullable=False),
        sa.Column("has_accessories", sa.Boolean(), nullable=False),
        sa.Column("powers_on", sa.Boolean(), nullable=False),
        sa.Column("quote_low_paise", sa.Integer(), nullable=True),
        sa.Column("quote_high_paise", sa.Integer(), nullable=True),
        sa.Column("customer_name", sa.String(120), nullable=False),
        sa.Column("contact", sa.String(160), nullable=False),
        sa.Column("city", sa.String(80), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exchange_leads")),
    )


def downgrade() -> None:
    op.drop_table("exchange_leads")
