"""Add additional storage metadata to uploads

Revision ID: 7f3ac33e86e7
Revises: 9ea41f46e661
Create Date: 2021-11-08 10:52:39.551416
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "7f3ac33e86e7"
down_revision = "9ea41f46e661"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("upload", sa.Column("calculated_checksum", sa.Text(), nullable=True))

    op.add_column(
        "upload",
        sa.Column("storage_type", sa.Text(), nullable=False, server_default="local"),
    )
    op.alter_column("upload", "storage_type", server_default=None)

    op.add_column(
        "upload",
        sa.Column("upload_type", sa.Text(), nullable=False, server_default="chunked"),
    )
    op.alter_column("upload", "upload_type", server_default=None)


def downgrade():
    op.drop_column("upload", "upload_type")
    op.drop_column("upload", "storage_type")
    op.drop_column("upload", "calculated_checksum")
