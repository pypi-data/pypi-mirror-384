"""Add collaborator role

Revision ID: 59a964c2b247
Revises: 7f3ac33e86e7
Create Date: 2021-11-19 09:37:47.258922
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "59a964c2b247"
down_revision = "7f3ac33e86e7"
branch_labels = None
depends_on = None


def _upgrade_resources(conn, resource_type):
    # Collect and iterate through all existing resources of the given resource type.
    resources = conn.execute(
        sa.text(
            """
            SELECT id
            FROM {resource}
            """.format(
                resource=resource_type
            )
        )
    )

    for resource in resources:
        # Add the "collaborator" role itself to each resource.
        role = conn.execute(
            sa.text(
                """
                INSERT INTO role (name, object, object_id)
                VALUES ('collaborator', '{resource}', {resource_id})
                RETURNING id
                """.format(
                    resource=resource_type, resource_id=resource.id
                )
            )
        ).fetchone()

        # Collect the permissions needed for the new "collaborator" role.
        permissions = conn.execute(
            sa.text(
                """
                SELECT id
                FROM permission
                WHERE action IN ('read', 'link')
                      AND object='{resource}'
                      AND object_id={resource_id}
                """.format(
                    resource=resource_type, resource_id=resource.id
                )
            )
        )

        # Add the collected permissions to the new "collaborator" role.
        for permission in permissions:
            op.execute(
                """
                INSERT INTO role_permission (role_id, permission_id)
                VALUES ({role_id}, {permission_id})
                """.format(
                    role_id=role.id, permission_id=permission.id
                )
            )


def upgrade():
    conn = op.get_bind()

    # Add the new "collaborator" role to all existing resources.
    _upgrade_resources(conn, "record")
    _upgrade_resources(conn, "collection")


def _downgrade_resources(conn, resource_type):
    # Handle all roles of both users and groups.
    for subject_type in ["user_role", "group_role"]:
        # Collect all existing "collaborator" roles of the given resource type.
        collab_roles = conn.execute(
            sa.text(
                """
                SELECT role.id, role.object_id
                FROM {subject}
                JOIN role ON role.id={subject}.role_id
                WHERE role.name='collaborator' AND role.object='{resource}'
                """.format(
                    subject=subject_type, resource=resource_type
                )
            )
        )

        for collab_role in collab_roles:
            # For each existing "collaborator" role, get the corresponding "member" role
            # of the same resource.
            member_role = conn.execute(
                sa.text(
                    """
                    SELECT id
                    FROM role
                    WHERE name='member'
                          AND object='{resource}'
                          AND object_id={object_id}
                    """.format(
                        resource=resource_type, object_id=collab_role.object_id
                    )
                )
            ).fetchone()

            # Replace the existing "collaborator" role with the old "member" role.
            op.execute(
                """
                UPDATE {subject}
                SET role_id={member_role_id}
                WHERE role_id={collab_role_id}
                """.format(
                    subject=subject_type,
                    member_role_id=member_role.id,
                    collab_role_id=collab_role.id,
                )
            )

    # Remove the "collaborator" role of all existing resources of the given resource
    # type.
    op.execute(
        """
        DELETE FROM role_permission
        WHERE role_id IN (
            SELECT id
            FROM role
            WHERE name='collaborator' AND object='{resource}'
        )
        """.format(
            resource=resource_type
        )
    )

    op.execute(
        """
        DELETE FROM role
        WHERE name='collaborator' AND object='{resource}'
        """.format(
            resource=resource_type
        )
    )


def downgrade():
    conn = op.get_bind()

    # Change all existing "collaborator" roles of users and groups to "member" roles.
    _downgrade_resources(conn, "record")
    _downgrade_resources(conn, "collection")
