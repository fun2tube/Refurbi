"""return requests

Revision ID: 0020
Revises: 0019
"""

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "return_requests",
        sa.Column("id", ID, nullable=False),
        sa.Column("order_item_id", ID, sa.ForeignKey("order_items.id"), nullable=False),
        sa.Column("order_id", ID, sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("refund_paise", sa.Integer(), nullable=False),
        sa.Column("refund_ref", sa.String(64), nullable=True),
        sa.Column("admin_note", sa.String(300), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_return_requests")),
        sa.UniqueConstraint("order_item_id", name=op.f("uq_return_requests_order_item_id")),
    )
    op.create_index(op.f("ix_return_requests_order_id"), "return_requests", ["order_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_return_requests_order_id"), table_name="return_requests")
    op.drop_table("return_requests")
