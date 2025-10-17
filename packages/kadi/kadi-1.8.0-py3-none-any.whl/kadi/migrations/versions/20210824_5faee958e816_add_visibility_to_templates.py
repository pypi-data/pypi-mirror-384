"""Add visibility to templates

Revision ID: 5faee958e816
Revises: 3ad85ecad1b3
Create Date: 2021-08-24 10:39:32.931436
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "5faee958e816"
down_revision = "3ad85ecad1b3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "template",
        sa.Column("visibility", sa.Text(), nullable=False, server_default="private"),
    )
    op.alter_column("template", "visibility", server_default=None)
    op.create_index(
        op.f("ix_template_visibility"), "template", ["visibility"], unique=False
    )
    op.create_check_constraint(
        "ck_visibility_values", "template", "visibility IN ('private', 'public')"
    )


def downgrade():
    op.drop_index(op.f("ix_template_visibility"), table_name="template")
    op.drop_column("template", "visibility")
