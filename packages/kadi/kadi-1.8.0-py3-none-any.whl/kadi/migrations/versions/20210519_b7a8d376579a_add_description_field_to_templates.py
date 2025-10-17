"""Add description field to templates

Revision ID: b7a8d376579a
Revises: 4f05f776c206
Create Date: 2021-05-19 10:32:19.379215
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "b7a8d376579a"
down_revision = "4f05f776c206"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "template",
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
    )
    op.alter_column("template", "description", server_default=None)
    op.create_check_constraint(
        "ck_description_length", "template", "char_length(description) <= 10000"
    )

    op.add_column(
        "template",
        sa.Column("plain_description", sa.Text(), nullable=False, server_default=""),
    )
    op.alter_column("template", "plain_description", server_default=None)


def downgrade():
    op.drop_column("template", "plain_description")
    op.drop_column("template", "description")
