"""Add user_id to record links

Revision ID: eb281611a8be
Revises: 6cfd8369030f
Create Date: 2022-09-06 15:22:43.760481
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "eb281611a8be"
down_revision = "6cfd8369030f"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Create the column as nullable first.
    op.add_column("record_link", sa.Column("user_id", sa.Integer(), nullable=True))

    # Update all existing record links by simply taking the user ID of the outgoing
    # record as creator.
    record_links = conn.execute(
        sa.text(
            """
            SELECT id, record_from_id
            FROM record_link
            """
        )
    )

    for record_link in record_links:
        record = conn.execute(
            sa.text(
                """
                SELECT user_id
                FROM record
                WHERE id={record_id}
                """.format(
                    record_id=record_link.record_from_id
                )
            )
        ).fetchone()

        op.execute(
            """
            UPDATE record_link
            SET user_id={user_id}
            WHERE id={record_link_id}
            """.format(
                user_id=record.user_id, record_link_id=record_link.id
            )
        )

    # Now the column can safely be changed to be nullable.
    op.alter_column(
        "record_link", "user_id", existing_type=sa.Integer(), nullable=False
    )

    op.create_foreign_key(
        op.f("fk_record_link_user_id_user"), "record_link", "user", ["user_id"], ["id"]
    )


def downgrade():
    op.drop_constraint(
        op.f("fk_record_link_user_id_user"), "record_link", type_="foreignkey"
    )
    op.drop_column("record_link", "user_id")
