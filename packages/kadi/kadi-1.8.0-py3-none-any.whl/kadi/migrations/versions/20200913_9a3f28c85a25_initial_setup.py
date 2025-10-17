"""Initial setup

Revision ID: 9a3f28c85a25
Revises:
Create Date: 2020-09-13 00:11:39.566128
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import kadi.lib.migration_types


# revision identifiers, used by Alembic.
revision = "9a3f28c85a25"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "permission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("object", sa.Text(), nullable=False),
        sa.Column("object_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permission")),
        sa.UniqueConstraint(
            "action",
            "object",
            "object_id",
            name="uq_permission_action_object_object_id",
        ),
    )
    op.create_index(
        "ix_action_object", "permission", ["action", "object"], unique=False
    )
    op.create_table(
        "role",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("object", sa.Text(), nullable=True),
        sa.Column("object_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "(object IS NULL AND object_id IS NULL) OR (object IS NOT NULL AND"
            " object_id IS NOT NULL)",
            name="ck_system_role",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role")),
        sa.UniqueConstraint(
            "name", "object", "object_id", name="uq_role_name_object_object_id"
        ),
    )
    op.create_index(
        "ix_object_object_id", "role", ["object", "object_id"], unique=False
    )
    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.CheckConstraint("char_length(name) <= 50", name="ck_name_length"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tag")),
    )
    op.create_index(op.f("ix_tag_name"), "tag", ["name"], unique=True)
    op.create_table(
        "user",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("about", sa.Text(), nullable=False),
        sa.Column("image_name", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email_is_private", sa.Boolean(), nullable=False),
        sa.Column("new_user_id", sa.Integer(), nullable=True),
        sa.Column("latest_identity_id", sa.Integer(), nullable=True),
        sa.Column("state", sa.Text(), nullable=False),
        sa.CheckConstraint("state IN ('active', 'inactive')", name="ck_state_values"),
        sa.CheckConstraint("char_length(about) <= 10000", name="ck_about_length"),
        sa.ForeignKeyConstraint(
            ["latest_identity_id"],
            ["identity.id"],
            name=op.f("fk_user_latest_identity_id_identity"),
            use_alter=True,
        ),
        sa.ForeignKeyConstraint(
            ["new_user_id"], ["user.id"], name=op.f("fk_user_new_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user")),
    )
    op.create_index(op.f("ix_user_state"), "user", ["state"], unique=False)
    op.create_table(
        "access_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=True),
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column("expires_at", kadi.lib.migration_types.UTCDateTime(), nullable=True),
        sa.CheckConstraint("char_length(name) <= 150", name="ck_name_length"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_access_token_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_access_token")),
    )
    op.create_index(
        op.f("ix_access_token_token_hash"), "access_token", ["token_hash"], unique=False
    )
    op.create_table(
        "collection",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("plain_description", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("visibility", sa.Text(), nullable=False),
        sa.CheckConstraint("state IN ('active', 'deleted')", name="ck_state_values"),
        sa.CheckConstraint(
            "visibility IN ('private', 'public')", name="ck_visibility_values"
        ),
        sa.CheckConstraint(
            "char_length(description) <= 10000", name="ck_description_length"
        ),
        sa.CheckConstraint(
            "char_length(identifier) <= 50", name="ck_identifier_length"
        ),
        sa.CheckConstraint("char_length(title) <= 150", name="ck_title_length"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_collection_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collection")),
    )
    op.create_index(
        op.f("ix_collection_identifier"), "collection", ["identifier"], unique=True
    )
    op.create_index(op.f("ix_collection_state"), "collection", ["state"], unique=False)
    op.create_index(
        op.f("ix_collection_visibility"), "collection", ["visibility"], unique=False
    )
    op.create_table(
        "group",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("plain_description", sa.Text(), nullable=False),
        sa.Column("image_name", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("visibility", sa.Text(), nullable=False),
        sa.CheckConstraint("state IN ('active', 'deleted')", name="ck_state_values"),
        sa.CheckConstraint(
            "visibility IN ('private', 'public')", name="ck_visibility_values"
        ),
        sa.CheckConstraint(
            "char_length(description) <= 10000", name="ck_description_length"
        ),
        sa.CheckConstraint(
            "char_length(identifier) <= 50", name="ck_identifier_length"
        ),
        sa.CheckConstraint("char_length(title) <= 150", name="ck_title_length"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_group_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_group")),
    )
    op.create_index(op.f("ix_group_identifier"), "group", ["identifier"], unique=True)
    op.create_index(op.f("ix_group_state"), "group", ["state"], unique=False)
    op.create_index(op.f("ix_group_visibility"), "group", ["visibility"], unique=False)
    op.create_table(
        "identity",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_identity_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_identity")),
    )
    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_notification_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notification")),
    )
    op.create_index(
        "ix_user_id_name", "notification", ["user_id", "name"], unique=False
    )
    op.create_table(
        "record",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("plain_description", sa.Text(), nullable=False),
        sa.Column(
            "extras",
            kadi.lib.migration_types.ExtrasJSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("visibility", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "state IN ('active', 'deleted', 'purged')", name="ck_state_values"
        ),
        sa.CheckConstraint(
            "visibility IN ('private', 'public')", name="ck_visibility_values"
        ),
        sa.CheckConstraint(
            "char_length(description) <= 10000", name="ck_description_length"
        ),
        sa.CheckConstraint(
            "char_length(identifier) <= 50", name="ck_identifier_length"
        ),
        sa.CheckConstraint("char_length(title) <= 150", name="ck_title_length"),
        sa.CheckConstraint("char_length(type) <= 50", name="ck_type_length"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_record_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_record")),
    )
    op.create_index(op.f("ix_record_identifier"), "record", ["identifier"], unique=True)
    op.create_index(op.f("ix_record_state"), "record", ["state"], unique=False)
    op.create_index(
        op.f("ix_record_visibility"), "record", ["visibility"], unique=False
    )
    op.create_table(
        "revision",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_revision_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revision")),
    )
    op.create_table(
        "role_permission",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permission.id"],
            name=op.f("fk_role_permission_permission_id_permission"),
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["role.id"], name=op.f("fk_role_permission_role_id_role")
        ),
        sa.PrimaryKeyConstraint(
            "role_id", "permission_id", name=op.f("pk_role_permission")
        ),
    )
    op.create_table(
        "task",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("arguments", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint(
            "state IN ('pending', 'running', 'revoked', 'success', 'failure')",
            name="ck_state_values",
        ),
        sa.CheckConstraint(
            "progress >= 0 AND progress <= 100", name="ck_progress_range"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_task_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task")),
    )
    op.create_index(op.f("ix_task_state"), "task", ["state"], unique=False)
    op.create_index(
        "ix_user_id_name_state", "task", ["user_id", "name", "state"], unique=False
    )
    op.create_table(
        "template",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column(
            "data",
            kadi.lib.migration_types.ExtrasJSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.CheckConstraint("type IN ('record', 'extras')", name="ck_type_values"),
        sa.CheckConstraint(
            "char_length(identifier) <= 50", name="ck_identifier_length"
        ),
        sa.CheckConstraint("char_length(title) <= 150", name="ck_title_length"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_template_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_template")),
    )
    op.create_index(
        op.f("ix_template_identifier"), "template", ["identifier"], unique=True
    )
    op.create_index(op.f("ix_template_type"), "template", ["type"], unique=False)
    op.create_table(
        "user_permission",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permission.id"],
            name=op.f("fk_user_permission_permission_id_permission"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_user_permission_user_id_user")
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "permission_id", name=op.f("pk_user_permission")
        ),
    )
    op.create_table(
        "user_role",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"], ["role.id"], name=op.f("fk_user_role_role_id_role")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_user_role_user_id_user")
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id", name=op.f("pk_user_role")),
    )
    op.create_table(
        "workflow",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("char_length(name) <= 150", name="ck_name_length"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_workflow_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workflow")),
    )
    op.create_table(
        "access_token_scope",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("access_token_id", sa.Integer(), nullable=False),
        sa.Column("object", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["access_token_id"],
            ["access_token.id"],
            name=op.f("fk_access_token_scope_access_token_id_access_token"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_access_token_scope")),
    )
    op.create_table(
        "collection_revision",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("revision_id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.Column("collection_revision_id", sa.Integer(), nullable=True),
        sa.Column("identifier", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=True),
        sa.Column("visibility", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["collection.id"],
            name=op.f("fk_collection_revision_collection_id_collection"),
        ),
        sa.ForeignKeyConstraint(
            ["collection_revision_id"],
            ["collection_revision.id"],
            name=op.f(
                "fk_collection_revision_collection_revision_id_collection_revision"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["revision.id"],
            name=op.f("fk_collection_revision_revision_id_revision"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collection_revision")),
    )
    op.create_table(
        "collection_tag",
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["collection.id"],
            name=op.f("fk_collection_tag_collection_id_collection"),
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"], ["tag.id"], name=op.f("fk_collection_tag_tag_id_tag")
        ),
        sa.PrimaryKeyConstraint(
            "collection_id", "tag_id", name=op.f("pk_collection_tag")
        ),
    )
    op.create_table(
        "file",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("mimetype", sa.Text(), nullable=False),
        sa.Column("magic_mimetype", sa.Text(), nullable=True),
        sa.Column("checksum", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("storage_type", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "state IN ('active', 'inactive', 'deleted')", name="ck_state_values"
        ),
        sa.CheckConstraint("storage_type IN ('local')", name="ck_storage_type_values"),
        sa.CheckConstraint("char_length(checksum) <= 256", name="ck_checksum_length"),
        sa.CheckConstraint("char_length(mimetype) <= 256", name="ck_mimetype_length"),
        sa.CheckConstraint("char_length(name) <= 256", name="ck_name_length"),
        sa.CheckConstraint("size >= 0", name="ck_size_range"),
        sa.ForeignKeyConstraint(
            ["record_id"], ["record.id"], name=op.f("fk_file_record_id_record")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_file_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file")),
    )
    op.create_index(op.f("ix_file_state"), "file", ["state"], unique=False)
    op.create_index(
        "uq_file_record_id_name",
        "file",
        ["record_id", "name"],
        unique=True,
        postgresql_where=sa.text("state = 'active'"),
    )
    op.create_table(
        "group_collection",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["collection.id"],
            name=op.f("fk_group_collection_collection_id_collection"),
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["group.id"], name=op.f("fk_group_collection_group_id_group")
        ),
        sa.PrimaryKeyConstraint(
            "group_id", "collection_id", name=op.f("pk_group_collection")
        ),
    )
    op.create_table(
        "group_permission",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"], ["group.id"], name=op.f("fk_group_permission_group_id_group")
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permission.id"],
            name=op.f("fk_group_permission_permission_id_permission"),
        ),
        sa.PrimaryKeyConstraint(
            "group_id", "permission_id", name=op.f("pk_group_permission")
        ),
    )
    op.create_table(
        "group_record",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"], ["group.id"], name=op.f("fk_group_record_group_id_group")
        ),
        sa.ForeignKeyConstraint(
            ["record_id"], ["record.id"], name=op.f("fk_group_record_record_id_record")
        ),
        sa.PrimaryKeyConstraint("group_id", "record_id", name=op.f("pk_group_record")),
    )
    op.create_table(
        "group_revision",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("revision_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("group_revision_id", sa.Integer(), nullable=True),
        sa.Column("identifier", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=True),
        sa.Column("visibility", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["group_id"], ["group.id"], name=op.f("fk_group_revision_group_id_group")
        ),
        sa.ForeignKeyConstraint(
            ["group_revision_id"],
            ["group_revision.id"],
            name=op.f("fk_group_revision_group_revision_id_group_revision"),
        ),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["revision.id"],
            name=op.f("fk_group_revision_revision_id_revision"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_group_revision")),
    )
    op.create_table(
        "group_role",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"], ["group.id"], name=op.f("fk_group_role_group_id_group")
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["role.id"], name=op.f("fk_group_role_role_id_role")
        ),
        sa.PrimaryKeyConstraint("group_id", "role_id", name=op.f("pk_group_role")),
    )
    op.create_table(
        "ldap_identity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("displayname", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "char_length(displayname) <= 150", name="ck_displayname_length"
        ),
        sa.ForeignKeyConstraint(
            ["id"], ["identity.id"], name=op.f("fk_ldap_identity_id_identity")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ldap_identity")),
    )
    op.create_index(
        op.f("ix_ldap_identity_username"), "ldap_identity", ["username"], unique=True
    )
    op.create_table(
        "local_identity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("displayname", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("email_confirmed", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "char_length(displayname) <= 150", name="ck_displayname_length"
        ),
        sa.CheckConstraint("char_length(email) <= 256", name="ck_email_length"),
        sa.CheckConstraint(
            "char_length(username) >= 3 AND char_length(username) <= 50",
            name="ck_username_length",
        ),
        sa.ForeignKeyConstraint(
            ["id"], ["identity.id"], name=op.f("fk_local_identity_id_identity")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_local_identity")),
    )
    op.create_index(
        op.f("ix_local_identity_username"), "local_identity", ["username"], unique=True
    )
    op.create_table(
        "record_collection",
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["collection.id"],
            name=op.f("fk_record_collection_collection_id_collection"),
        ),
        sa.ForeignKeyConstraint(
            ["record_id"],
            ["record.id"],
            name=op.f("fk_record_collection_record_id_record"),
        ),
        sa.PrimaryKeyConstraint(
            "record_id", "collection_id", name=op.f("pk_record_collection")
        ),
    )
    op.create_table(
        "record_link",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("record_from_id", sa.Integer(), nullable=False),
        sa.Column("record_to_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.CheckConstraint("char_length(name) <= 150", name="ck_name_length"),
        sa.ForeignKeyConstraint(
            ["record_from_id"],
            ["record.id"],
            name=op.f("fk_record_link_record_from_id_record"),
        ),
        sa.ForeignKeyConstraint(
            ["record_to_id"],
            ["record.id"],
            name=op.f("fk_record_link_record_to_id_record"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_record_link")),
    )
    op.create_table(
        "record_revision",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("revision_id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("record_revision_id", sa.Integer(), nullable=True),
        sa.Column("identifier", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("type", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "extras",
            kadi.lib.migration_types.ExtrasJSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("state", sa.Text(), nullable=True),
        sa.Column("visibility", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["record_id"],
            ["record.id"],
            name=op.f("fk_record_revision_record_id_record"),
        ),
        sa.ForeignKeyConstraint(
            ["record_revision_id"],
            ["record_revision.id"],
            name=op.f("fk_record_revision_record_revision_id_record_revision"),
        ),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["revision.id"],
            name=op.f("fk_record_revision_revision_id_revision"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_record_revision")),
    )
    op.create_table(
        "record_tag",
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["record_id"], ["record.id"], name=op.f("fk_record_tag_record_id_record")
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"], ["tag.id"], name=op.f("fk_record_tag_tag_id_tag")
        ),
        sa.PrimaryKeyConstraint("record_id", "tag_id", name=op.f("pk_record_tag")),
    )
    op.create_table(
        "shib_identity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("displayname", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "char_length(displayname) <= 150", name="ck_displayname_length"
        ),
        sa.ForeignKeyConstraint(
            ["id"], ["identity.id"], name=op.f("fk_shib_identity_id_identity")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shib_identity")),
    )
    op.create_index(
        op.f("ix_shib_identity_username"), "shib_identity", ["username"], unique=True
    )
    op.create_table(
        "temporary_file",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("mimetype", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.CheckConstraint("state IN ('active', 'inactive')", name="ck_state_values"),
        sa.CheckConstraint("char_length(mimetype) <= 256", name="ck_mimetype_length"),
        sa.CheckConstraint("char_length(name) <= 256", name="ck_name_length"),
        sa.CheckConstraint("size >= 0", name="ck_size_range"),
        sa.ForeignKeyConstraint(
            ["record_id"],
            ["record.id"],
            name=op.f("fk_temporary_file_record_id_record"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_temporary_file_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_temporary_file")),
    )
    op.create_index(
        op.f("ix_temporary_file_state"), "temporary_file", ["state"], unique=False
    )
    op.create_table(
        "file_revision",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("revision_id", sa.Integer(), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_revision_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("size", sa.BigInteger(), nullable=True),
        sa.Column("mimetype", sa.Text(), nullable=True),
        sa.Column("checksum", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["file_id"], ["file.id"], name=op.f("fk_file_revision_file_id_file")
        ),
        sa.ForeignKeyConstraint(
            ["file_revision_id"],
            ["file_revision.id"],
            name=op.f("fk_file_revision_file_revision_id_file_revision"),
        ),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["revision.id"],
            name=op.f("fk_file_revision_revision_id_revision"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file_revision")),
    )
    op.create_table(
        "upload",
        sa.Column("created_at", kadi.lib.migration_types.UTCDateTime(), nullable=False),
        sa.Column(
            "last_modified", kadi.lib.migration_types.UTCDateTime(), nullable=False
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("mimetype", sa.Text(), nullable=False),
        sa.Column("checksum", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "state IN ('active', 'inactive', 'processing')", name="ck_state_values"
        ),
        sa.CheckConstraint("char_length(checksum) <= 256", name="ck_checksum_length"),
        sa.CheckConstraint("char_length(mimetype) <= 256", name="ck_mimetype_length"),
        sa.CheckConstraint("char_length(name) <= 256", name="ck_name_length"),
        sa.CheckConstraint("chunk_count >= 1", name="ck_chunk_count_range"),
        sa.CheckConstraint("size >= 0", name="ck_size_range"),
        sa.ForeignKeyConstraint(
            ["file_id"], ["file.id"], name=op.f("fk_upload_file_id_file")
        ),
        sa.ForeignKeyConstraint(
            ["record_id"], ["record.id"], name=op.f("fk_upload_record_id_record")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_upload_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_upload")),
    )
    op.create_index(op.f("ix_upload_state"), "upload", ["state"], unique=False)
    op.create_table(
        "chunk",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("upload_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("index", sa.Integer(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.CheckConstraint("state IN ('active', 'inactive')", name="ck_state_values"),
        sa.CheckConstraint("index >= 0", name="ck_index_range"),
        sa.CheckConstraint("size >= 0", name="ck_size_range"),
        sa.ForeignKeyConstraint(
            ["upload_id"], ["upload.id"], name=op.f("fk_chunk_upload_id_upload")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chunk")),
        sa.UniqueConstraint("upload_id", "index", name="uq_chunk_upload_id_index"),
    )
    op.create_index(op.f("ix_chunk_state"), "chunk", ["state"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_chunk_state"), table_name="chunk")
    op.drop_table("chunk")
    op.drop_index(op.f("ix_upload_state"), table_name="upload")
    op.drop_table("upload")
    op.drop_table("file_revision")
    op.drop_index(op.f("ix_temporary_file_state"), table_name="temporary_file")
    op.drop_table("temporary_file")
    op.drop_index(op.f("ix_shib_identity_username"), table_name="shib_identity")
    op.drop_table("shib_identity")
    op.drop_table("record_tag")
    op.drop_table("record_revision")
    op.drop_table("record_link")
    op.drop_table("record_collection")
    op.drop_index(op.f("ix_local_identity_username"), table_name="local_identity")
    op.drop_table("local_identity")
    op.drop_index(op.f("ix_ldap_identity_username"), table_name="ldap_identity")
    op.drop_table("ldap_identity")
    op.drop_table("group_role")
    op.drop_table("group_revision")
    op.drop_table("group_record")
    op.drop_table("group_permission")
    op.drop_table("group_collection")
    op.drop_index("uq_file_record_id_name", table_name="file")
    op.drop_index(op.f("ix_file_state"), table_name="file")
    op.drop_table("file")
    op.drop_table("collection_tag")
    op.drop_table("collection_revision")
    op.drop_table("access_token_scope")
    op.drop_table("workflow")
    op.drop_table("user_role")
    op.drop_table("user_permission")
    op.drop_index(op.f("ix_template_type"), table_name="template")
    op.drop_index(op.f("ix_template_identifier"), table_name="template")
    op.drop_table("template")
    op.drop_index("ix_user_id_name_state", table_name="task")
    op.drop_index(op.f("ix_task_state"), table_name="task")
    op.drop_table("task")
    op.drop_table("role_permission")
    op.drop_table("revision")
    op.drop_index(op.f("ix_record_visibility"), table_name="record")
    op.drop_index(op.f("ix_record_state"), table_name="record")
    op.drop_index(op.f("ix_record_identifier"), table_name="record")
    op.drop_table("record")
    op.drop_index("ix_user_id_name", table_name="notification")
    op.drop_table("notification")
    op.drop_table("identity")
    op.drop_index(op.f("ix_group_visibility"), table_name="group")
    op.drop_index(op.f("ix_group_state"), table_name="group")
    op.drop_index(op.f("ix_group_identifier"), table_name="group")
    op.drop_table("group")
    op.drop_index(op.f("ix_collection_visibility"), table_name="collection")
    op.drop_index(op.f("ix_collection_state"), table_name="collection")
    op.drop_index(op.f("ix_collection_identifier"), table_name="collection")
    op.drop_table("collection")
    op.drop_index(op.f("ix_access_token_token_hash"), table_name="access_token")
    op.drop_table("access_token")
    op.drop_index(op.f("ix_user_state"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_tag_name"), table_name="tag")
    op.drop_table("tag")
    op.drop_index("ix_object_object_id", table_name="role")
    op.drop_table("role")
    op.drop_index("ix_action_object", table_name="permission")
    op.drop_table("permission")
