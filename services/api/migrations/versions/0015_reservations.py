"""reservations and email otps

Revision ID: 0015
Revises: 0014
"""

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "email_otps",
        sa.Column("id", ID, nullable=False),
        sa.Column("email", sa.String(160), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_otps")),
    )
    op.create_index(op.f("ix_email_otps_email"), "email_otps", ["email"])
    op.create_table(
        "reservations",
        sa.Column("id", ID, nullable=False),
        sa.Column("code", sa.String(12), nullable=False),
        sa.Column("device_id", ID, sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("counter_id", ID, nullable=True),
        sa.Column("customer_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(160), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reservations")),
        sa.UniqueConstraint("code", name=op.f("uq_reservations_code")),
    )
    op.create_index(op.f("ix_reservations_device_id"), "reservations", ["device_id"])


def downgrade() -> None:
    op.drop_table("reservations")
    op.drop_table("email_otps")
