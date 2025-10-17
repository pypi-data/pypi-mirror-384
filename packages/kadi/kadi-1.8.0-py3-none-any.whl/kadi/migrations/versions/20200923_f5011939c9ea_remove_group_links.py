"""Remove group links

Revision ID: f5011939c9ea
Revises: 9a3f28c85a25
Create Date: 2020-09-23 16:54:07.254293
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "f5011939c9ea"
down_revision = "9a3f28c85a25"
branch_labels = None
depends_on = None


def upgrade():
    # Remove all possible group link permissions.
    op.execute(
        """
        DELETE FROM role_permission
        WHERE permission_id IN (
            SELECT id
            FROM permission
            WHERE action='link' AND object='group'
        )
        """
    )

    op.execute(
        """
        DELETE FROM permission
        WHERE action='link' AND object='group'
        """
    )

    op.drop_table("group_record")
    op.drop_table("group_collection")

    # This was somehow not applied via the initial migration script.
    op.create_foreign_key(
        op.f("fk_user_latest_identity_id_identity"),
        "user",
        "identity",
        ["latest_identity_id"],
        ["id"],
        use_alter=True,
    )


def downgrade():
    conn = op.get_bind()

    # Add back the global link group permission for the "admin" system role if it
    # exists, i.e. if the database was initialized beforehand.
    role = conn.execute(
        sa.text(
            """
            SELECT id
            FROM role
            WHERE name='admin' AND object IS NULL AND object_id IS NULL
            """
        )
    ).fetchone()

    if role is not None:
        permission = conn.execute(
            sa.text(
                """
                INSERT INTO permission (action, object, object_id)
                VALUES ('link', 'group', NULL)
                RETURNING id
                """
            )
        ).fetchone()

        op.execute(
            """
            INSERT INTO role_permission (role_id, permission_id)
            VALUES ({role_id}, {permission_id})
            """.format(
                role_id=role.id, permission_id=permission.id
            )
        )

    # Add back the regular link group permissions for existing groups for the "editor"
    # and "admin" roles.
    groups = conn.execute(
        sa.text(
            """
            SELECT id
            FROM "group"
            """
        )
    )

    for group in groups:
        permission = conn.execute(
            sa.text(
                """
                INSERT INTO permission (action, object, object_id)
                VALUES ('link', 'group', {object_id})
                RETURNING id
                """.format(
                    object_id=group.id
                )
            )
        ).fetchone()

        roles = conn.execute(
            sa.text(
                """
                SELECT id
                FROM role
                WHERE name IN ('editor', 'admin')
                      AND object='group'
                      AND object_id={object_id}
                """.format(
                    object_id=group.id
                )
            )
        )

        for role in roles:
            op.execute(
                """
                INSERT INTO role_permission (role_id, permission_id)
                VALUES ({role_id}, {permission_id})
                """.format(
                    role_id=role.id, permission_id=permission.id
                )
            )

    op.drop_constraint(
        op.f("fk_user_latest_identity_id_identity"), "user", type_="foreignkey"
    )

    op.create_table(
        "group_collection",
        sa.Column("group_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("collection_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["collection.id"],
            name="fk_group_collection_collection_id_collection",
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["group.id"], name="fk_group_collection_group_id_group"
        ),
        sa.PrimaryKeyConstraint(
            "group_id", "collection_id", name="pk_group_collection"
        ),
    )
    op.create_table(
        "group_record",
        sa.Column("group_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("record_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"], ["group.id"], name="fk_group_record_group_id_group"
        ),
        sa.ForeignKeyConstraint(
            ["record_id"], ["record.id"], name="fk_group_record_record_id_record"
        ),
        sa.PrimaryKeyConstraint("group_id", "record_id", name="pk_group_record"),
    )
