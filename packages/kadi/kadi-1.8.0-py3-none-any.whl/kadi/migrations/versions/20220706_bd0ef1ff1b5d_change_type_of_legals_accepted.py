"""Change type of legals_accepted

Revision ID: bd0ef1ff1b5d
Revises: 35b7244f26dc
Create Date: 2022-07-06 11:54:48.533620
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "bd0ef1ff1b5d"
down_revision = "35b7244f26dc"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    users = conn.execute(
        sa.text(
            """
            SELECT id, legals_accepted
            FROM "user"
            """
        )
    )

    op.drop_column("user", "legals_accepted")
    op.add_column(
        "user",
        sa.Column(
            "legals_accepted", kadi.lib.migration_types.UTCDateTime(), nullable=True
        ),
    )

    # Set the acceptance date to the current one for all users that accepted the legal
    # notices before.
    for user in users:
        if user.legals_accepted:
            op.execute(
                """
                UPDATE "user"
                SET legals_accepted=now() at time zone 'utc'
                WHERE id={user_id}
                """.format(
                    user_id=user.id
                )
            )


def downgrade():
    conn = op.get_bind()

    users = conn.execute(
        sa.text(
            """
            SELECT id, legals_accepted
            FROM "user"
            """
        )
    )

    op.drop_column("user", "legals_accepted")
    op.add_column(
        "user",
        sa.Column(
            "legals_accepted",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=False,
            server_default="False",
        ),
    )
    op.alter_column("user", "legals_accepted", server_default=None)

    # Set the acceptance flag for all users that accepted the legal notices before
    # (independent of date).
    for user in users:
        if user.legals_accepted is not None:
            op.execute(
                """
                UPDATE "user"
                SET legals_accepted=TRUE
                WHERE id={user_id}
                """.format(
                    user_id=user.id
                )
            )
