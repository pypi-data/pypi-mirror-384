"""Add missing check constraints

Revision ID: eb107333faa2
Revises: 45e1107a36be
Create Date: 2022-07-18 09:15:33.827213
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "eb107333faa2"
down_revision = "45e1107a36be"
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint(
        "ck_description_length", "file", "char_length(description) <= 10000"
    )
    op.create_check_constraint(
        "ck_description_length", "upload", "char_length(description) <= 10000"
    )
    op.create_check_constraint(
        "ck_state_values", "template", "state IN ('active', 'deleted')"
    )


def downgrade():
    op.drop_constraint("ck_state_values", "template", type_="check")
    op.drop_constraint("ck_description_length", "upload", type_="check")
    op.drop_constraint("ck_description_length", "file", type_="check")
