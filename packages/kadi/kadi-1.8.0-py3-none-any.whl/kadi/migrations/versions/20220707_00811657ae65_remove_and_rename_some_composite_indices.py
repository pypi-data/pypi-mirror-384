"""Remove and rename some composite indices

Revision ID: 00811657ae65
Revises: bd0ef1ff1b5d
Create Date: 2022-07-07 17:10:41.888540
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "00811657ae65"
down_revision = "bd0ef1ff1b5d"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER INDEX ix_user_id_name RENAME TO ix_notification_user_id_name")
    op.execute("ALTER INDEX ix_role_id_type RENAME TO ix_role_rule_role_id_type")
    op.execute("ALTER INDEX ix_user_id_name_state RENAME TO ix_task_user_id_name_state")

    op.drop_index("ix_action_object", table_name="permission")
    op.drop_index("ix_object_object_id", table_name="role")


def downgrade():
    op.create_index(
        "ix_object_object_id", "role", ["object", "object_id"], unique=False
    )
    op.create_index(
        "ix_action_object", "permission", ["action", "object"], unique=False
    )

    op.execute("ALTER INDEX ix_notification_user_id_name RENAME TO ix_user_id_name")
    op.execute("ALTER INDEX ix_role_rule_role_id_type RENAME TO ix_role_id_type")
    op.execute("ALTER INDEX ix_task_user_id_name_state RENAME TO ix_user_id_name_state")
