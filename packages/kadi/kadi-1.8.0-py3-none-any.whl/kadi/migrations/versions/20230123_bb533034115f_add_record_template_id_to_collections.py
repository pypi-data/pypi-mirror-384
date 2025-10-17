"""Add record_template_id to collections

Revision ID: bb533034115f
Revises: e27c706115f1
Create Date: 2023-01-23 11:03:32.712656
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "bb533034115f"
down_revision = "e27c706115f1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("collection", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("record_template_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_collection_record_template_id_template"),
            "template",
            ["record_template_id"],
            ["id"],
        )

    with op.batch_alter_table("collection_revision", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "record_template",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            )
        )


def downgrade():
    with op.batch_alter_table("collection_revision", schema=None) as batch_op:
        batch_op.drop_column("record_template")

    with op.batch_alter_table("collection", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_collection_record_template_id_template"), type_="foreignkey"
        )
        batch_op.drop_column("record_template_id")
