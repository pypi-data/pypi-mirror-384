"""Add OIDC identity table

Revision ID: 8a79ad55f1ba
Revises: e55fe6980554
Create Date: 2023-11-17 20:36:27.247442
"""

import sqlalchemy as sa
from alembic import op

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "8a79ad55f1ba"
down_revision = "e55fe6980554"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "oidc_identity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("email_confirmed", sa.Boolean(), nullable=False),
        sa.Column("issuer", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.CheckConstraint("char_length(email) <= 256", name="ck_email_length"),
        sa.CheckConstraint(
            "char_length(username) >= 3 AND char_length(username) <= 50",
            name="ck_username_length",
        ),
        sa.ForeignKeyConstraint(
            ["id"], ["identity.id"], name=op.f("fk_oidc_identity_id_identity")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oidc_identity")),
        sa.UniqueConstraint(
            "issuer", "subject", name="uq_oidc_identity_issuer_subject"
        ),
    )

    with op.batch_alter_table("oidc_identity", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_oidc_identity_username"), ["username"], unique=True
        )


def downgrade():
    with op.batch_alter_table("oidc_identity", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_oidc_identity_username"))

    op.drop_table("oidc_identity")

    # Delete all references to any associated base identities.
    op.execute(
        """
        UPDATE "user"
        SET latest_identity_id=NULL
        WHERE latest_identity_id IN (
            SELECT id
            FROM identity
            WHERE type='oidc'
        )
        """
    )

    # Finally, delete the associated base identities.
    op.execute(
        """
        DELETE FROM identity
        WHERE type='oidc'
        """
    )
