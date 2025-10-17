"""Add ORCID to users

Revision ID: a8755f77a809
Revises: c50a6efaa783
Create Date: 2023-07-06 15:50:34.507922
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "a8755f77a809"
down_revision = "c50a6efaa783"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("orcid", sa.Text(), nullable=True))
        batch_op.create_check_constraint("ck_orcid_length", "char_length(orcid) <= 19")


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("orcid")
