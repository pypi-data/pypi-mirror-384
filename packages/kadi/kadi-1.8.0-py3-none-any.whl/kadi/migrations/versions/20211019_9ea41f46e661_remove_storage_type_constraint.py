"""Remove storage_type constraint

Revision ID: 9ea41f46e661
Revises: 251515abdbd9
Create Date: 2021-10-19 13:07:13.668009
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "9ea41f46e661"
down_revision = "251515abdbd9"
branch_labels = None
depends_on = None


def upgrade():
    # Only remove the constraint if it actually exists.
    op.execute("ALTER TABLE file DROP CONSTRAINT IF EXISTS ck_storage_type_values")


def downgrade():
    # Do not re-add the constraint here, since this could potentially lead to various
    # types of conflicts when using custom storages.
    pass
