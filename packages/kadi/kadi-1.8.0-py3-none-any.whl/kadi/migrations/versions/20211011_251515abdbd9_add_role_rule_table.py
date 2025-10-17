"""Add role_rule table

Revision ID: 251515abdbd9
Revises: b6e17ffc8d23
Create Date: 2021-10-11 16:03:49.831710
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "251515abdbd9"
down_revision = "b6e17ffc8d23"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "role_rule",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("condition", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"], ["role.id"], name=op.f("fk_role_rule_role_id_role")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_rule")),
    )
    op.create_index("ix_role_id_type", "role_rule", ["role_id", "type"], unique=False)


def downgrade():
    op.drop_index("ix_role_id_type", table_name="role_rule")
    op.drop_table("role_rule")
