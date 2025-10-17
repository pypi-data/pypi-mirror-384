"""Add saved_search table

Revision ID: 0809e253ab7e
Revises: 0ac40f65eb23
Create Date: 2023-01-18 12:49:32.688902
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "0809e253ab7e"
down_revision = "0ac40f65eb23"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "saved_search",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("object", sa.Text(), nullable=False),
        sa.Column("query_string", sa.Text(), nullable=False),
        sa.CheckConstraint("char_length(name) <= 150", name="ck_name_length"),
        sa.CheckConstraint(
            "char_length(query_string) <= 4096", name="ck_query_string_length"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_saved_search_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_saved_search")),
    )

    with op.batch_alter_table("saved_search", schema=None) as batch_op:
        batch_op.create_index(
            "ix_saved_search_user_id_object", ["user_id", "object"], unique=False
        )


def downgrade():
    with op.batch_alter_table("saved_search", schema=None) as batch_op:
        batch_op.drop_index("ix_saved_search_user_id_object")

    op.drop_table("saved_search")
