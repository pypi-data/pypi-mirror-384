"""Adjust upload and chunk tables

Revision ID: 097b6463808c
Revises: 8a79ad55f1ba
Create Date: 2024-01-10 10:48:56.760646
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "097b6463808c"
down_revision = "8a79ad55f1ba"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("chunk", schema=None) as batch_op:
        batch_op.add_column(sa.Column("checksum", sa.Text(), nullable=True))
        batch_op.create_check_constraint(
            "ck_checksum_length", "char_length(checksum) <= 256"
        )

    with op.batch_alter_table("upload", schema=None) as batch_op:
        batch_op.drop_column("calculated_checksum")

        batch_op.alter_column("description", existing_type=sa.TEXT(), nullable=True)
        batch_op.alter_column("mimetype", existing_type=sa.TEXT(), nullable=True)

        batch_op.create_check_constraint(
            "ck_upload_type_values", "upload_type IN ('direct', 'chunked')"
        )


def downgrade():
    with op.batch_alter_table("upload", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "calculated_checksum", sa.TEXT(), autoincrement=False, nullable=True
            )
        )
        batch_op.create_check_constraint(
            "ck_calculated_checksum_length", "char_length(calculated_checksum) <= 256"
        )

        batch_op.execute(
            """
            UPDATE upload
            SET mimetype='application/octet-stream'
            WHERE mimetype is NULL
            """
        )
        batch_op.alter_column("mimetype", existing_type=sa.TEXT(), nullable=False)

        batch_op.execute(
            """
            UPDATE upload
            SET description=''
            WHERE description is NULL
            """
        )
        batch_op.alter_column("description", existing_type=sa.TEXT(), nullable=False)

        batch_op.drop_constraint("ck_upload_type_values", type_="check")

    with op.batch_alter_table("chunk", schema=None) as batch_op:
        batch_op.drop_column("checksum")
