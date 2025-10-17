"""Remove permission tables

Revision ID: 5f4f2a054cfa
Revises: 097b6463808c
Create Date: 2024-04-02 10:52:25.271435
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "5f4f2a054cfa"
down_revision = "097b6463808c"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("user_permission")
    op.drop_table("group_permission")
    op.drop_table("role_permission")
    op.drop_table("permission")


def _get_or_create_permission(conn, action, object_name, object_id):
    permission = conn.execute(
        sa.text(
            """
            SELECT id
            FROM permission
            WHERE action=:action AND object=:object AND object_id{condition}
            """.format(
                condition=f"={object_id}" if object_id is not None else " is NULL"
            )
        ),
        action=action,
        object=object_name,
    ).fetchone()

    if permission is None:
        return conn.execute(
            sa.text(
                """
                INSERT INTO permission (action, object, object_id)
                VALUES (:action, :object, :object_id)
                RETURNING id
                """
            ),
            action=action,
            object=object_name,
            object_id=object_id,
        ).fetchone()

    return permission


def _setup_system_role_permissions(conn):
    # Add back all global permissions to the corresponding system roles if they exist,
    # i.e. if the database was initialized beforehand.
    system_roles = {
        "admin": {
            "record": ["create", "read", "update", "link", "permissions", "delete"],
            "collection": ["create", "read", "update", "link", "permissions", "delete"],
            "template": ["create", "read", "update", "permissions", "delete"],
            "group": ["create", "read", "update", "members", "delete"],
        },
        "member": {
            "record": ["create"],
            "collection": ["create"],
            "template": ["create"],
            "group": ["create"],
        },
        "guest": {},
    }

    for system_role_name, system_role_meta in system_roles.items():
        system_role = conn.execute(
            sa.text(
                """
                SELECT id
                FROM role
                WHERE name=:name AND object IS NULL AND object_id is NULL
                """
            ),
            name=system_role_name,
        ).fetchone()

        if not system_role:
            continue

        for object_name, actions in system_role_meta.items():
            for action in actions:
                permission = _get_or_create_permission(conn, action, object_name, None)
                conn.execute(
                    sa.text(
                        """
                        INSERT INTO role_permission (role_id, permission_id)
                        VALUES (:role_id, :permission_id)
                        """
                    ),
                    role_id=system_role.id,
                    permission_id=permission.id,
                )


def _setup_resource_role_permissions(conn):
    # Add back all resource permissions to the corresponding roles.
    resource_roles = {
        "record": {
            "member": ["read"],
            "collaborator": ["read", "link"],
            "editor": ["read", "link", "update"],
            "admin": ["read", "link", "update", "permissions", "delete"],
        },
        "collection": {
            "member": ["read"],
            "collaborator": ["read", "link"],
            "editor": ["read", "link", "update"],
            "admin": ["read", "link", "update", "permissions", "delete"],
        },
        "template": {
            "member": ["read"],
            "editor": ["read", "update"],
            "admin": ["read", "update", "permissions", "delete"],
        },
        "group": {
            "member": ["read"],
            "editor": ["read", "update"],
            "admin": ["read", "update", "members", "delete"],
        },
    }

    for object_name, roles in resource_roles.items():
        resources = conn.execute(
            sa.text(
                """
                SELECT id
                FROM "{table}"
                """.format(
                    table=object_name
                )
            )
        )

        for resource in resources:
            for role_name, actions in roles.items():
                role = conn.execute(
                    sa.text(
                        """
                        SELECT id
                        FROM role
                        WHERE name=:name AND object=:object AND object_id=:object_id
                        """
                    ),
                    name=role_name,
                    object=object_name,
                    object_id=resource.id,
                ).fetchone()

                for action in actions:
                    permission = _get_or_create_permission(
                        conn, action, object_name, resource.id
                    )
                    conn.execute(
                        sa.text(
                            """
                            INSERT INTO role_permission (role_id, permission_id)
                            VALUES (:role_id, :permission_id)
                            """
                        ),
                        role_id=role.id,
                        permission_id=permission.id,
                    )


def downgrade():
    op.create_table(
        "permission",
        sa.Column(
            "id",
            sa.INTEGER(),
            server_default=sa.text("nextval('permission_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("action", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("object", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("object_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_permission"),
        sa.UniqueConstraint(
            "action",
            "object",
            "object_id",
            name="uq_permission_action_object_object_id",
        ),
        postgresql_ignore_search_path=False,
    )
    op.create_table(
        "role_permission",
        sa.Column("role_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("permission_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permission.id"],
            name="fk_role_permission_permission_id_permission",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["role.id"], name="fk_role_permission_role_id_role"
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name="pk_role_permission"),
    )
    op.create_table(
        "group_permission",
        sa.Column("group_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("permission_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"], ["group.id"], name="fk_group_permission_group_id_group"
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permission.id"],
            name="fk_group_permission_permission_id_permission",
        ),
        sa.PrimaryKeyConstraint(
            "group_id", "permission_id", name="pk_group_permission"
        ),
    )
    op.create_table(
        "user_permission",
        sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("permission_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permission.id"],
            name="fk_user_permission_permission_id_permission",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name="fk_user_permission_user_id_user"
        ),
        sa.PrimaryKeyConstraint("user_id", "permission_id", name="pk_user_permission"),
    )

    # Set up all system role and resource permissions again.
    conn = op.get_bind()

    _setup_system_role_permissions(conn)
    _setup_resource_role_permissions(conn)
