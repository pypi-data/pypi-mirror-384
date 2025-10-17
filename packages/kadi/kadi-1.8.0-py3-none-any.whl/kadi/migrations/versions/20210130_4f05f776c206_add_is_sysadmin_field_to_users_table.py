"""Add is_sysadmin field to users table

Revision ID: 4f05f776c206
Revises: e3bdf50ef41b
Create Date: 2021-01-30 17:09:21.981930
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "4f05f776c206"
down_revision = "e3bdf50ef41b"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("identity", "user_id", existing_type=sa.INTEGER(), nullable=True)
    op.add_column(
        "user",
        sa.Column("is_sysadmin", sa.Boolean(), nullable=False, server_default="False"),
    )
    op.alter_column("user", "is_sysadmin", server_default=None)

    op.drop_constraint("ck_state_values", "user", type_="check")
    op.create_check_constraint(
        "ck_state_values",
        "user",
        "state IN ('active', 'inactive', 'deleted')",
    )


def downgrade():
    # Set any potential leftover "deleted" states to "inactive".
    op.execute(
        """
        UPDATE "user"
        SET state='inactive'
        WHERE state='deleted'
        """
    )
    op.drop_constraint("ck_state_values", "user", type_="check")
    op.create_check_constraint(
        "ck_state_values",
        "user",
        "state IN ('active', 'inactive')",
    )

    op.drop_column("user", "is_sysadmin")
    # Should not cause any issues, as identities always have an associated user.
    op.alter_column("identity", "user_id", existing_type=sa.INTEGER(), nullable=False)
