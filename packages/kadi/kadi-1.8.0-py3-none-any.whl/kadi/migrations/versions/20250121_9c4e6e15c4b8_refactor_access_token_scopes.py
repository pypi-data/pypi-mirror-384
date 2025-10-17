"""Refactor access token scopes

Revision ID: 9c4e6e15c4b8
Revises: 5f4f2a054cfa
Create Date: 2025-01-21 16:36:56.731618
"""

import json

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "9c4e6e15c4b8"
down_revision = "5f4f2a054cfa"
branch_labels = None
depends_on = None


# All scope values that are available at this point.
SCOPES = [
    "record.create",
    "record.read",
    "record.link",
    "record.update",
    "record.permissions",
    "record.delete",
    "collection.create",
    "collection.read",
    "collection.link",
    "collection.update",
    "collection.permissions",
    "collection.delete",
    "template.create",
    "template.read",
    "template.update",
    "template.permissions",
    "template.delete",
    "group.create",
    "group.read",
    "group.update",
    "group.members",
    "group.delete",
    "user.read",
    "misc.manage_trash",
]


def _upgrade_scope(conn, tablename, scope):
    conn.execute(
        sa.text(
            """
            UPDATE {tablename}
            SET scope=:scope
            WHERE scope is NULL
            """.format(
                tablename=tablename
            )
        ),
        scope=scope,
    )

    with op.batch_alter_table(tablename, schema=None) as batch_op:
        batch_op.alter_column("scope", existing_type=sa.TEXT(), nullable=False)


def upgrade():
    conn = op.get_bind()
    scope = " ".join(sorted(SCOPES))

    _upgrade_scope(conn, "oauth2_server_auth_code", scope)
    _upgrade_scope(conn, "oauth2_server_token", scope)
    _upgrade_scope(conn, "personal_token", scope)

    # OAuth2 clients need separate handling, as scopes are stored as part of its JSON
    # metadata.
    conn.execute(
        sa.text(
            """
            UPDATE oauth2_server_client
            SET client_metadata=jsonb_set(client_metadata, '{scope}', :scope)
            WHERE client_metadata->'scope'='null'::jsonb;
            """
        ),
        scope=json.dumps(scope),
    )


def _downgrade_scope(tablename):
    # We keep the actual scope values unchanged, as the semantics between no scopes
    # (before the upgrade) and all scopes are almost the same.
    with op.batch_alter_table(tablename, schema=None) as batch_op:
        batch_op.alter_column("scope", existing_type=sa.TEXT(), nullable=True)


def downgrade():
    _downgrade_scope("personal_token")
    _downgrade_scope("oauth2_server_token")
    _downgrade_scope("oauth2_server_auth_code")
