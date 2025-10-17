"""Add template revision table

Revision ID: 35b7244f26dc
Revises: 6f3ff009bda7
Create Date: 2022-06-28 13:19:12.630411
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "35b7244f26dc"
down_revision = "6f3ff009bda7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "template_revision",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("revision_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("template_revision_id", sa.Integer(), nullable=True),
        sa.Column("identifier", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("visibility", sa.Text(), nullable=True),
        sa.Column(
            "data",
            kadi.lib.migration_types.ExtrasJSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("state", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["revision.id"],
            name=op.f("fk_template_revision_revision_id_revision"),
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["template.id"],
            name=op.f("fk_template_revision_template_id_template"),
        ),
        sa.ForeignKeyConstraint(
            ["template_revision_id"],
            ["template_revision.id"],
            name=op.f("fk_template_revision_template_revision_id_template_revision"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_template_revision")),
    )


def downgrade():
    op.drop_table("template_revision")
