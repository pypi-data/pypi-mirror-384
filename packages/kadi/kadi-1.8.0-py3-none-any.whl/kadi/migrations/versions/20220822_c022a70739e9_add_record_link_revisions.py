"""Add record link revisions

Revision ID: c022a70739e9
Revises: 98715dda7501
Create Date: 2022-08-22 14:28:03.643972
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "c022a70739e9"
down_revision = "98715dda7501"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "record_revision",
        sa.Column("links_to", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "record_revision",
        sa.Column(
            "linked_from", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )


def downgrade():
    op.drop_column("record_revision", "linked_from")
    op.drop_column("record_revision", "links_to")
