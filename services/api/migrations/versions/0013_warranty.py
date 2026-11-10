"""warranty

Revision ID: 0013
Revises: 0012
"""

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "warranties",
        sa.Column("id", ID, nullable=False),
        sa.Column("sale_id", ID, sa.ForeignKey("sales.id"), nullable=False),
        sa.Column("invoice_id", ID, sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("device_id", ID, sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("months", sa.Integer(), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sale_id"),
        sa.UniqueConstraint("invoice_id"),
    )
    op.create_index("ix_warranties_device_id", "warranties", ["device_id"])
    op.create_table(
        "warranty_claims",
        sa.Column("id", ID, nullable=False),
        sa.Column("warranty_id", ID, sa.ForeignKey("warranties.id"), nullable=False),
        sa.Column("issue", sa.Text(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("resolution_note", sa.Text(), nullable=False),
        sa.Column("created_by", ID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_warranty_claims_warranty_id", "warranty_claims", ["warranty_id"])


def downgrade() -> None:
    op.drop_table("warranty_claims")
    op.drop_table("warranties")
