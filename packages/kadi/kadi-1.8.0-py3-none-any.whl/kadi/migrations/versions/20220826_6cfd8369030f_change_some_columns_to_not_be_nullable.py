"""Change some columns to not be nullable

Revision ID: 6cfd8369030f
Revises: c022a70739e9
Create Date: 2022-08-26 10:52:18.855652
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "6cfd8369030f"
down_revision = "c022a70739e9"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "access_token", "token_hash", existing_type=sa.TEXT(), nullable=False
    )
    op.alter_column(
        "local_identity", "password_hash", existing_type=sa.TEXT(), nullable=False
    )


def downgrade():
    op.alter_column(
        "local_identity", "password_hash", existing_type=sa.TEXT(), nullable=True
    )
    op.alter_column(
        "access_token", "token_hash", existing_type=sa.TEXT(), nullable=True
    )
