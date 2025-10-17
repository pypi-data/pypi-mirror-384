"""Add last_used field to access tokens

Revision ID: d815323c120c
Revises: f5011939c9ea
Create Date: 2020-10-23 09:56:13.133155
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "d815323c120c"
down_revision = "f5011939c9ea"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "access_token",
        sa.Column("last_used", kadi.lib.migration_types.UTCDateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("access_token", "last_used")
