"""Add description to files and uploads

Revision ID: 45e1107a36be
Revises: 00811657ae65
Create Date: 2022-07-15 14:38:21.957635
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "45e1107a36be"
down_revision = "00811657ae65"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "file", sa.Column("description", sa.Text(), nullable=False, server_default="")
    )
    op.alter_column("file", "description", server_default=None)

    op.add_column("file_revision", sa.Column("description", sa.Text(), nullable=True))

    op.add_column(
        "upload", sa.Column("description", sa.Text(), nullable=False, server_default="")
    )
    op.alter_column("upload", "description", server_default=None)


def downgrade():
    op.drop_column("upload", "description")
    op.drop_column("file_revision", "description")
    op.drop_column("file", "description")
