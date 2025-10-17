"""Add term to record links

Revision ID: 0ac40f65eb23
Revises: eb281611a8be
Create Date: 2022-10-16 14:07:13.863633
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "0ac40f65eb23"
down_revision = "eb281611a8be"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("record_link", sa.Column("term", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_term_length", "record_link", "char_length(term) <= 2048"
    )


def downgrade():
    op.drop_column("record_link", "term")
