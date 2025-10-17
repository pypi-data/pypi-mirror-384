"""Add state to templates

Revision ID: 6f3ff009bda7
Revises: 131469c4b12e
Create Date: 2022-06-24 13:02:55.079155
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "6f3ff009bda7"
down_revision = "131469c4b12e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "template",
        sa.Column("state", sa.Text(), nullable=False, server_default="active"),
    )
    op.alter_column("template", "state", server_default=None)
    op.create_index(op.f("ix_template_state"), "template", ["state"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_template_state"), table_name="template")
    op.drop_column("template", "state")
