"""Add oauth2_token table

Revision ID: 3ad696720c9b
Revises: d815323c120c
Create Date: 2020-11-05 08:59:18.593158
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "3ad696720c9b"
down_revision = "d815323c120c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "oauth2_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "access_token",
            kadi.lib.migration_types.StringEncryptedType(),
            nullable=False,
        ),
        sa.Column(
            "refresh_token",
            kadi.lib.migration_types.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("expires_at", kadi.lib.migration_types.UTCDateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_oauth2_token_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth2_token")),
        sa.UniqueConstraint("user_id", "name", name="uq_oauth2_token_user_id_name"),
    )


def downgrade():
    op.drop_table("oauth2_token")
