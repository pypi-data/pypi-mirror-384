"""Add legals_accepted to users

Revision ID: 96a656b04d3e
Revises: 1ecbff3941c6
Create Date: 2022-03-31 17:32:12.195915
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "96a656b04d3e"
down_revision = "1ecbff3941c6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "legals_accepted", sa.Boolean(), nullable=False, server_default="False"
        ),
    )
    op.alter_column("user", "legals_accepted", server_default=None)


def downgrade():
    op.drop_column("user", "legals_accepted")
