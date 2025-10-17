"""Refactor access token tables

Revision ID: 099c37f9e47c
Revises: bb533034115f
Create Date: 2023-02-06 11:14:04.378104
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "099c37f9e47c"
down_revision = "bb533034115f"
branch_labels = None
depends_on = None


def _rename_table(op, prev_name, new_name):
    # Rename the table, primary key, primary key sequence and user ID foreign key.
    op.rename_table(prev_name, new_name)

    with op.batch_alter_table(new_name, schema=None) as batch_op:
        batch_op.execute(
            "ALTER INDEX pk_{prev_name} RENAME TO pk_{new_name}".format(
                prev_name=prev_name, new_name=new_name
            )
        )
        batch_op.execute(
            "ALTER SEQUENCE {prev_name}_id_seq RENAME TO {new_name}_id_seq".format(
                prev_name=prev_name, new_name=new_name
            )
        )
        batch_op.execute(
            """
            ALTER TABLE {new_name}
            RENAME CONSTRAINT fk_{prev_name}_user_id_user
                TO fk_{new_name}_user_id_user
            """.format(
                prev_name=prev_name, new_name=new_name
            )
        )


def _rename_oauth2_client_token_table(op, prev_name, new_name):
    _rename_table(op, prev_name, new_name)

    with op.batch_alter_table(new_name, schema=None) as batch_op:
        batch_op.execute(
            """
            ALTER INDEX uq_{prev_name}_user_id_name
            RENAME TO uq_{new_name}_user_id_name
            """.format(
                prev_name=prev_name, new_name=new_name
            )
        )


def _rename_personal_token_table(op, prev_name, new_name):
    _rename_table(op, prev_name, new_name)

    with op.batch_alter_table(new_name, schema=None) as batch_op:
        batch_op.execute(
            """
            ALTER INDEX ix_{prev_name}_token_hash
            RENAME TO ix_{new_name}_token_hash
            """.format(
                prev_name=prev_name, new_name=new_name
            )
        )


def upgrade():
    conn = op.get_bind()

    # Rename the table for OAuth2 client tokens.
    _rename_oauth2_client_token_table(op, "oauth2_token", "oauth2_client_token")

    # Rename the table for personal tokens.
    _rename_personal_token_table(op, "access_token", "personal_token")

    # Add the new scope column to the personal token table.
    op.add_column("personal_token", sa.Column("scope", sa.Text(), nullable=True))

    # Migrate the existing personal token scopes.
    tokens = conn.execute(
        sa.text(
            """
            SELECT id
            FROM personal_token
            """
        )
    )

    for token in tokens:
        scopes = conn.execute(
            sa.text(
                """
                SELECT object, action
                FROM access_token_scope
                WHERE access_token_id={token_id}
                """.format(
                    token_id=token.id
                )
            )
        )
        scope_value = " ".join(
            sorted(f"{scope.object}.{scope.action}" for scope in scopes)
        )

        if scope_value:
            op.execute(
                """
                UPDATE personal_token
                SET scope='{scope_value}'
                WHERE id={token_id}
                """.format(
                    scope_value=scope_value, token_id=token.id
                )
            )

    # Drop the table for personal token scopes.
    op.drop_table("access_token_scope")


def downgrade():
    conn = op.get_bind()

    # Rename the table for personal tokens.
    _rename_personal_token_table(op, "personal_token", "access_token")

    # Create the table for personal token scopes.
    op.create_table(
        "access_token_scope",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("access_token_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("object", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("action", sa.TEXT(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["access_token_id"],
            ["access_token.id"],
            name="fk_access_token_scope_access_token_id_access_token",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_access_token_scope"),
    )

    # Migrate the existing personal token scopes.
    tokens = conn.execute(
        sa.text(
            """
            SELECT id, scope
            FROM access_token
            """
        )
    )

    for token in tokens:
        if token.scope:
            for scope in token.scope.split():
                object, action = scope.split(".", 1)
                op.execute(
                    """
                    INSERT INTO access_token_scope (access_token_id, object, action)
                    VALUES ({token_id}, '{object}', '{action}')
                    """.format(
                        token_id=token.id, object=object, action=action
                    )
                )

    # Remove the scope column of the personal token table.
    op.drop_column("access_token", "scope")

    # Rename the table for OAuth2 client tokens.
    _rename_oauth2_client_token_table(op, "oauth2_client_token", "oauth2_token")
