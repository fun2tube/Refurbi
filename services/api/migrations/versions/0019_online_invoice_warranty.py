"""warranties.sale_id nullable (online orders have no counter sale)

Revision ID: 0019
Revises: 0018
"""

import sqlalchemy as sa
from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None

ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    with op.batch_alter_table("warranties") as b:
        b.alter_column("sale_id", existing_type=ID, nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("warranties") as b:
        b.alter_column("sale_id", existing_type=ID, nullable=False)
