"""Add license table

Revision ID: dc589906a474
Revises: 3ad696720c9b
Create Date: 2020-11-07 13:21:29.915750
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "dc589906a474"
down_revision = "3ad696720c9b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "license",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_license")),
        sa.UniqueConstraint("name", name=op.f("uq_license_name")),
    )
    op.add_column("record", sa.Column("license_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_record_license_id_license"),
        "record",
        "license",
        ["license_id"],
        ["id"],
    )
    op.add_column(
        "record_revision",
        sa.Column("license", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade():
    op.drop_column("record_revision", "license")
    op.drop_constraint(
        op.f("fk_record_license_id_license"), "record", type_="foreignkey"
    )
    op.drop_column("record", "license_id")
    op.drop_table("license")
