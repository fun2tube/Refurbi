"""payments and payment events

Revision ID: 0017
Revises: 0016
"""

import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", ID, nullable=False),
        sa.Column("checkout_id", ID, sa.ForeignKey("checkouts.id"), nullable=False),
        sa.Column("gateway", sa.String(12), nullable=False),
        sa.Column("gateway_order_id", sa.String(64), nullable=False),
        sa.Column("gateway_payment_id", sa.String(64), nullable=True),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
        sa.UniqueConstraint("gateway_order_id", name=op.f("uq_payments_gateway_order_id")),
    )
    op.create_index(op.f("ix_payments_checkout_id"), "payments", ["checkout_id"])
    op.create_table(
        "payment_events",
        sa.Column("id", ID, nullable=False),
        sa.Column("event_id", sa.String(80), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_events")),
        sa.UniqueConstraint("event_id", name=op.f("uq_payment_events_event_id")),
    )


def downgrade() -> None:
    op.drop_table("payment_events")
    op.drop_table("payments")
