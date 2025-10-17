"""Add favorite table

Revision ID: 98715dda7501
Revises: eb107333faa2
Create Date: 2022-07-27 10:23:52.793695
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "98715dda7501"
down_revision = "eb107333faa2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "favorite",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("object", sa.Text(), nullable=False),
        sa.Column("object_id", sa.Integer(), nullable=False),
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_favorite_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_favorite")),
        sa.UniqueConstraint(
            "user_id",
            "object",
            "object_id",
            name="uq_favorite_user_id_object_object_id",
        ),
    )


def downgrade():
    op.drop_table("favorite")
