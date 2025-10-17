"""Add config_item table

Revision ID: 1ecbff3941c6
Revises: 59a964c2b247
Create Date: 2021-12-15 09:19:46.021334
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "1ecbff3941c6"
down_revision = "59a964c2b247"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "config_item",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_config_item_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_config_item")),
    )
    op.create_index("ix_key_user_id", "config_item", ["key", "user_id"], unique=False)


def downgrade():
    op.drop_index("ix_key_user_id", table_name="config_item")
    op.drop_table("config_item")
