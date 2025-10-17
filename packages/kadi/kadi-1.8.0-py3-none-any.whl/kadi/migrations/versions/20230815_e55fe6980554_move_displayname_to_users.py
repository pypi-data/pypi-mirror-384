"""Move displayname to users

Revision ID: e55fe6980554
Revises: a8755f77a809
Create Date: 2023-08-15 08:43:13.580109
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "e55fe6980554"
down_revision = "a8755f77a809"
branch_labels = None
depends_on = None


IDENTITY_TABLES = {
    "local": "local_identity",
    "ldap": "ldap_identity",
    "shib": "shib_identity",
}


def upgrade():
    conn = op.get_bind()

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("displayname", sa.Text(), nullable=False, server_default="")
        )
        batch_op.create_check_constraint(
            "ck_displayname_length", "char_length(displayname) <= 150"
        )

    # Select all users that have not been merged.
    users = conn.execute(
        sa.text(
            """
            SELECT id
            FROM "user"
            WHERE new_user_id IS NULL
            """
        )
    )

    for user in users:
        # Select the last recently created (based on ID) base identity for each user.
        base_identity = conn.execute(
            sa.text(
                """
                SELECT DISTINCT ON (user_id) id, type
                FROM identity
                WHERE user_id=:user_id
                ORDER BY user_id, id DESC
                """
            ),
            user_id=user.id,
        ).fetchone()

        # Select the concrete identity.
        identity = conn.execute(
            sa.text(
                """
                SELECT displayname
                FROM {identity_table}
                WHERE id=:id
                """.format(
                    identity_table=IDENTITY_TABLES[base_identity.type],
                )
            ),
            id=base_identity.id,
        ).fetchone()

        # Update the user.
        conn.execute(
            sa.text(
                """
                UPDATE "user"
                SET displayname=left(:displayname, 150)
                WHERE id=:id
                """
            ),
            displayname=identity.displayname,
            id=user.id,
        )

    for tablename in IDENTITY_TABLES.values():
        with op.batch_alter_table(tablename, schema=None) as batch_op:
            batch_op.drop_column("displayname")

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("displayname", server_default=None)


def downgrade():
    conn = op.get_bind()

    for tablename in IDENTITY_TABLES.values():
        with op.batch_alter_table(tablename, schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "displayname",
                    sa.TEXT(),
                    autoincrement=False,
                    nullable=False,
                    server_default="",
                )
            )
            batch_op.create_check_constraint(
                "ck_displayname_length", "char_length(displayname) <= 150"
            )

    # Select all users that have not been merged.
    users = conn.execute(
        sa.text(
            """
            SELECT id, displayname
            FROM "user"
            WHERE new_user_id IS NULL
            """
        )
    )

    for user in users:
        # Select all base identities of the user.
        base_identities = conn.execute(
            sa.text(
                """
                SELECT id, type
                FROM identity
                WHERE user_id=:user_id
                """
            ),
            user_id=user.id,
        )

        for base_identity in base_identities:
            # Update each concrete identity.
            conn.execute(
                sa.text(
                    """
                    UPDATE {identity_table}
                    SET displayname=:displayname
                    WHERE id=:id
                    """.format(
                        identity_table=IDENTITY_TABLES[base_identity.type]
                    )
                ),
                displayname=user.displayname,
                id=base_identity.id,
            )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("displayname")

    for tablename in IDENTITY_TABLES.values():
        with op.batch_alter_table(tablename, schema=None) as batch_op:
            batch_op.alter_column("displayname", server_default=None)
