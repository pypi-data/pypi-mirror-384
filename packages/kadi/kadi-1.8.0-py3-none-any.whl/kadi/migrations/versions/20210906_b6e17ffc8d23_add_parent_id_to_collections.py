"""Add parent_id to collections

Revision ID: b6e17ffc8d23
Revises: 5faee958e816
Create Date: 2021-09-06 09:03:44.152745
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "b6e17ffc8d23"
down_revision = "5faee958e816"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("collection", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_collection_parent_id_collection"),
        "collection",
        "collection",
        ["parent_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        op.f("fk_collection_parent_id_collection"), "collection", type_="foreignkey"
    )
    op.drop_column("collection", "parent_id")
