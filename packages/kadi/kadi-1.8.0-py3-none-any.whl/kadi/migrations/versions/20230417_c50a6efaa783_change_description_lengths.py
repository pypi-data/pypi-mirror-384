"""Change description lengths

Revision ID: c50a6efaa783
Revises: a9babeb78f4e
Create Date: 2023-04-17 09:39:47.610713
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "c50a6efaa783"
down_revision = "a9babeb78f4e"
branch_labels = None
depends_on = None


TABLENAMES = ["record", "file", "upload", "collection", "template", "group"]


def _update_description_ck(tablename, length):
    description_ck = "ck_description_length"

    with op.batch_alter_table(tablename, schema=None) as batch_op:
        batch_op.drop_constraint(description_ck, type_="check")
        batch_op.create_check_constraint(
            description_ck, f"char_length(description) <= {length}"
        )


def upgrade():
    for tablename in TABLENAMES:
        _update_description_ck(tablename, 50_000)


def downgrade():
    length = 10_000

    for tablename in TABLENAMES:
        # We simply trim all descriptions that are too long.
        op.execute(
            """
            UPDATE "{tablename}"
            SET description=left(description, {length})
            WHERE char_length(description) > {length}
            """.format(
                tablename=tablename, length=length
            )
        )

        _update_description_ck(tablename, length)
