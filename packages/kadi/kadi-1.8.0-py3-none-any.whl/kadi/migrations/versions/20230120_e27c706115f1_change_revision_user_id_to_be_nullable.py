"""Change revision user_id to be nullable

Revision ID: e27c706115f1
Revises: 0809e253ab7e
Create Date: 2023-01-20 15:59:06.945001
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "e27c706115f1"
down_revision = "0809e253ab7e"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("revision", schema=None) as batch_op:
        batch_op.alter_column("user_id", existing_type=sa.INTEGER(), nullable=True)


def downgrade():
    # Do not make the column nullable again, as there is no good way to set the correct
    # user ID here.
    pass
