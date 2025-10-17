"""Remove orphaned revisions

Revision ID: e3bdf50ef41b
Revises: 4e644f9ae8c4
Create Date: 2021-01-28 09:48:23.873813
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "e3bdf50ef41b"
down_revision = "4e644f9ae8c4"
branch_labels = None
depends_on = None


def upgrade():
    # Delete all orphaned base revisions that might not have been deleted in the past.
    op.execute(
        """
        DELETE FROM revision
        WHERE id NOT IN (
            SELECT revision_id
            FROM record_revision
            UNION
            SELECT revision_id
            FROM file_revision
            UNION
            SELECT revision_id
            FROM collection_revision
            UNION
            SELECT revision_id
            FROM group_revision
        )
        """
    )


def downgrade():
    pass
