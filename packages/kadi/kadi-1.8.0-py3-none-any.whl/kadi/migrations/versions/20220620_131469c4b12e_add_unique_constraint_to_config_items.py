"""Add unique constraint to config items

Revision ID: 131469c4b12e
Revises: 96a656b04d3e
Create Date: 2022-06-20 09:22:57.084071
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "131469c4b12e"
down_revision = "96a656b04d3e"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_key_user_id", table_name="config_item")
    op.create_unique_constraint(
        "uq_config_item_key_user_id", "config_item", ["key", "user_id"]
    )


def downgrade():
    op.drop_constraint("uq_config_item_key_user_id", "config_item", type_="unique")
    op.create_index("ix_key_user_id", "config_item", ["key", "user_id"], unique=False)
