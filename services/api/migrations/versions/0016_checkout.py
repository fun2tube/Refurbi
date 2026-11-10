"""online checkout holds

Revision ID: 0016
Revises: 0015
"""

import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "checkouts",
        sa.Column("id", ID, nullable=False),
        sa.Column("token", sa.String(48), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("customer_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(160), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("address_line", sa.String(300), nullable=False),
        sa.Column("city", sa.String(80), nullable=False),
        sa.Column("pincode", sa.String(6), nullable=False),
        sa.Column("total_paise", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_checkouts")),
        sa.UniqueConstraint("token", name=op.f("uq_checkouts_token")),
    )
    op.create_table(
        "checkout_items",
        sa.Column("id", ID, nullable=False),
        sa.Column("checkout_id", ID, sa.ForeignKey("checkouts.id"), nullable=False),
        sa.Column("device_id", ID, sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("price_paise", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_checkout_items")),
    )
    op.create_index(op.f("ix_checkout_items_checkout_id"), "checkout_items", ["checkout_id"])
    op.create_index(op.f("ix_checkout_items_device_id"), "checkout_items", ["device_id"])


def downgrade() -> None:
    op.drop_table("checkout_items")
    op.drop_table("checkouts")
