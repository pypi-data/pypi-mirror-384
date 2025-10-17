"""Add OAuth2 server tables

Revision ID: a9babeb78f4e
Revises: 099c37f9e47c
Create Date: 2023-02-20 10:49:10.132934
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "a9babeb78f4e"
down_revision = "099c37f9e47c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "oauth2_server_client",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("client_id_issued_at", sa.Integer(), nullable=False),
        sa.Column("client_secret_expires_at", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("client_secret", sa.Text(), nullable=False),
        sa.Column(
            "client_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_oauth2_server_client_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth2_server_client")),
        sa.UniqueConstraint(
            "client_id", name=op.f("uq_oauth2_server_client_client_id")
        ),
    )

    op.create_table(
        "oauth2_server_auth_code",
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("redirect_uri", sa.Text(), nullable=True),
        sa.Column("response_type", sa.Text(), nullable=True),
        sa.Column("nonce", sa.Text(), nullable=True),
        sa.Column("auth_time", sa.Integer(), nullable=False),
        sa.Column("code_challenge", sa.Text(), nullable=True),
        sa.Column("code_challenge_method", sa.String(length=48), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["oauth2_server_client.client_id"],
            name=op.f("fk_oauth2_server_auth_code_client_id_oauth2_server_client"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_oauth2_server_auth_code_user_id_user"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth2_server_auth_code")),
        sa.UniqueConstraint("code", name=op.f("uq_oauth2_server_auth_code_code")),
    )

    op.create_table(
        "oauth2_server_token",
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(length=40), nullable=True),
        sa.Column("issued_at", sa.Integer(), nullable=False),
        sa.Column("access_token_revoked_at", sa.Integer(), nullable=False),
        sa.Column("refresh_token_revoked_at", sa.Integer(), nullable=False),
        sa.Column("expires_in", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["oauth2_server_client.client_id"],
            name=op.f("fk_oauth2_server_token_client_id_oauth2_server_client"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_oauth2_server_token_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth2_server_token")),
    )
    with op.batch_alter_table("oauth2_server_token", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_oauth2_server_token_access_token"),
            ["access_token"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_oauth2_server_token_refresh_token"),
            ["refresh_token"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("oauth2_server_token", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_oauth2_server_token_refresh_token"))
        batch_op.drop_index(batch_op.f("ix_oauth2_server_token_access_token"))

    op.drop_table("oauth2_server_token")
    op.drop_table("oauth2_server_auth_code")
    op.drop_table("oauth2_server_client")
