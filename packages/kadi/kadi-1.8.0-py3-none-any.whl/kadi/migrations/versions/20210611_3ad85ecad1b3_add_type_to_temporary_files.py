"""Add type to temporary files

Revision ID: 3ad85ecad1b3
Revises: b7a8d376579a
Create Date: 2021-06-11 14:34:54.705963
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "3ad85ecad1b3"
down_revision = "b7a8d376579a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("temporary_file", sa.Column("type", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("temporary_file", "type")
