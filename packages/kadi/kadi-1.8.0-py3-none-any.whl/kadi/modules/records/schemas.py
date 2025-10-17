# Copyright 2020 Karlsruhe Institute of Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from flask import has_request_context
from flask_login import current_user
from marshmallow import fields
from marshmallow import post_dump
from marshmallow import validates
from marshmallow import validates_schema
from marshmallow.validate import Length
from marshmallow.validate import OneOf
from marshmallow.validate import Range
from marshmallow.validate import ValidationError

import kadi.lib.constants as const
from kadi.lib.api.core import check_access_token_scopes
from kadi.lib.conversion import lower
from kadi.lib.conversion import normalize
from kadi.lib.conversion import strip
from kadi.lib.format import filesize
from kadi.lib.licenses.schemas import LicenseSchema
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.permissions.core import has_permission
from kadi.lib.resources.schemas import BaseResourceSchema
from kadi.lib.resources.schemas import check_duplicate_identifier
from kadi.lib.schemas import BaseSchema
from kadi.lib.schemas import CustomPluck
from kadi.lib.schemas import CustomString
from kadi.lib.schemas import validate_iri
from kadi.lib.schemas import validate_mimetype
from kadi.lib.tags.schemas import TagSchema
from kadi.lib.web import url_for
from kadi.modules.accounts.schemas import UserSchema
from kadi.modules.records.extras import ExtraSchema

from .models import Chunk
from .models import File
from .models import Record
from .models import RecordLink
from .models import Upload
from .models import UploadType


class RecordSchema(BaseResourceSchema):
    """Schema to represent records.

    See :class:`.Record`.

    :param previous_record: (optional) A record whose identifier should be excluded when
        checking for duplicates while deserializing.
    :param linked_collection: (optional) A collection that is linked to each record that
        should be serialized. Will be used to build endpoints for corresponding actions.
    :param is_template: (optional) Flag indicating whether the schema is used within the
        context of a template. Currently, this is only relevant for the extra metadata,
        see :class:`.ExtraSchema`.
    """

    type = CustomString(
        filter=[lower, normalize],
        allow_none=True,
        validate=Length(max=Record.Meta.check_constraints["type"]["length"]["max"]),
    )

    license = CustomPluck(LicenseSchema, "name", allow_none=True)

    tags = CustomPluck(TagSchema, "name", many=True)

    extras = fields.Method(
        "_serialize_extras", deserialize="_deserialize_extras", metadata={"many": True}
    )

    _links = fields.Method("_generate_links")

    _actions = fields.Method("_generate_actions")

    def __init__(
        self,
        previous_record=None,
        linked_collection=None,
        is_template=False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.previous_record = previous_record
        self.linked_collection = linked_collection
        self.is_template = is_template

    @validates("id")
    def _validate_id(self, value):
        if Record.query.get_active(value) is None:
            raise ValidationError("No record with this ID exists.")

    @validates("identifier")
    def _validate_identifier(self, value):
        check_duplicate_identifier(Record, value, exclude=self.previous_record)

    def _serialize_extras(self, obj):
        return obj.extras

    def _deserialize_extras(self, value):
        return ExtraSchema(is_template=self.is_template, many=True).load(value)

    def _generate_links(self, obj):
        links = {
            "self": url_for("api.get_record", id=obj.id),
            "files": url_for("api.get_files", id=obj.id),
            "download_files": url_for("api.download_files", id=obj.id),
            "uploads": url_for("api.get_uploads", id=obj.id),
            "collections": url_for("api.get_record_collections", id=obj.id),
            "records_to": url_for("api.get_record_links", id=obj.id, direction="out"),
            "records_from": url_for("api.get_record_links", id=obj.id, direction="in"),
            "user_roles": url_for("api.get_record_user_roles", id=obj.id),
            "group_roles": url_for("api.get_record_group_roles", id=obj.id),
            "revisions": url_for("api.get_record_revisions", id=obj.id),
            "file_revisions": url_for("api.get_file_revisions", id=obj.id),
        }

        if self._internal and self.linked_collection:
            links["view"] = url_for(
                "records.view_record", id=obj.id, collection=self.linked_collection.id
            )
        else:
            links["view"] = url_for("records.view_record", id=obj.id)

        return links

    def _generate_actions(self, obj):
        actions = {
            "edit": url_for("api.edit_record", id=obj.id),
            "delete": url_for("api.delete_record", id=obj.id),
            "new_upload": url_for("api.new_upload", id=obj.id),
            "link_record": url_for("api.new_record_link", id=obj.id),
            "link_collection": url_for("api.add_record_collection", id=obj.id),
            "add_user_role": url_for("api.add_record_user_role", id=obj.id),
            "add_group_role": url_for("api.add_record_group_role", id=obj.id),
        }

        if self.linked_collection:
            actions["remove_link"] = url_for(
                "api.remove_collection_record",
                collection_id=self.linked_collection.id,
                record_id=obj.id,
            )

        return actions


class RecordRevisionSchema(RecordSchema):
    """Schema to represent record revisions.

    Additionally includes the direct serialization of record links with a limited subset
    of attributes.
    """

    links_to = fields.Nested(
        "RecordLinkRevisionSchema",
        only=["id", "record_to_id", "name", "term"],
        many=True,
        dump_only=True,
    )

    linked_from = fields.Nested(
        "RecordLinkRevisionSchema",
        only=["id", "record_from_id", "name", "term"],
        many=True,
        dump_only=True,
    )


class RecordImportSchema(RecordSchema):
    """Schema to represent imported record data."""

    @validates("id")
    def _validate_id(self, value):
        pass

    @validates("identifier")
    def _validate_identifier(self, value):
        pass


class BaseRecordLinkSchema(BaseSchema):
    """Base schema class to represent record links."""

    name = CustomString(
        required=True,
        filter=normalize,
        validate=Length(max=RecordLink.Meta.check_constraints["name"]["length"]["max"]),
    )

    term = CustomString(
        filter=strip,
        load_default=None,
        validate=[
            Length(max=RecordLink.Meta.check_constraints["term"]["length"]["max"]),
            validate_iri,
        ],
    )


class RecordLinkSchema(BaseRecordLinkSchema):
    """Schema to represent record links.

    See :class:`.RecordLink`.

    :param current_record: (optional) The current record in whose context the record
        links are being serialized, in order to generate corresponding URLs to view or
        edit each record link. Only relevant for internal use.
    """

    id = fields.Integer(dump_only=True)

    created_at = fields.DateTime(dump_only=True)

    last_modified = fields.DateTime(dump_only=True)

    creator = fields.Nested(UserSchema, dump_only=True)

    record_from = fields.Nested(RecordSchema, dump_only=True)

    record_to = fields.Nested(RecordSchema, required=True)

    _links = fields.Method("_generate_links")

    _actions = fields.Method("_generate_actions")

    def __init__(self, current_record=None, **kwargs):
        super().__init__(**kwargs)

        self.current_record = current_record
        self.linkable_record_ids = None

        # Retrieve the linkable records of the current user in order to conditionally
        # include the internal edit links.
        if (
            self._internal
            and self.current_record is not None
            and has_request_context()
            and current_user.is_authenticated
        ):
            self.linkable_record_ids = {
                r.id
                for r in (
                    get_permitted_objects(current_user, "link", "record").with_entities(
                        Record.id
                    )
                )
            }

    @post_dump
    def _post_dump(self, data, **kwargs):
        if "creator" in data and not check_access_token_scopes("user.read"):
            del data["creator"]

        return data

    def _generate_links(self, obj):
        links = {
            "self": url_for(
                "api.get_record_link", record_id=obj.record_from_id, link_id=obj.id
            )
        }

        if self._internal and self.current_record is not None:
            links["view"] = url_for(
                "records.view_record_link",
                record_id=self.current_record.id,
                link_id=obj.id,
            )

            if not has_request_context() or (
                self.linkable_record_ids is not None
                and obj.record_from_id in self.linkable_record_ids
                and obj.record_to_id in self.linkable_record_ids
            ):
                links["edit"] = url_for(
                    "records.edit_record_link",
                    record_id=self.current_record.id,
                    link_id=obj.id,
                )

        return links

    def _generate_actions(self, obj):
        return {
            "edit": url_for(
                "api.edit_record_link", record_id=obj.record_from_id, link_id=obj.id
            ),
            "remove": url_for(
                "api.remove_record_link", record_id=obj.record_from_id, link_id=obj.id
            ),
        }


class RecordLinkDataSchema(BaseRecordLinkSchema):
    """Schema to represent the data of a generic record link in a certain direction.

    Mainly useful in combination with
    :func:`kadi.modules.records.links.create_record_links` and within templates.
    """

    direction = CustomString(required=True, validate=OneOf(["out", "in"]))

    record = fields.Integer(required=True, validate=Range(min=1))


class RecordLinkRevisionSchema(RecordLinkSchema):
    """Schema to represent record link revisions.

    Additionally includes the direct serialization of the IDs of the linked records.
    """

    record_from_id = fields.Integer(dump_only=True)

    record_to_id = fields.Integer(dump_only=True)


class FileSchema(BaseSchema):
    """Schema to represent files.

    See :class:`.File`.

    :param record: (optional) A record the file to be deserialized belongs to. Will be
        used to check for duplicate filenames while deserializing.
    :param previous_file: (optional) A file that will be excluded when checking for
        duplicate filenames while deserializing.
    """

    id = fields.String(dump_only=True)

    name = CustomString(
        required=True,
        filter=normalize,
        validate=Length(max=File.Meta.check_constraints["name"]["length"]["max"]),
    )

    description = CustomString(
        allow_ws_only=True,
        filter=strip,
        validate=Length(
            max=File.Meta.check_constraints["description"]["length"]["max"]
        ),
    )

    mimetype = CustomString(
        filter=[lower, normalize],
        validate=[
            Length(max=File.Meta.check_constraints["mimetype"]["length"]["max"]),
            validate_mimetype,
        ],
    )

    size = fields.Integer(dump_only=True)

    checksum = fields.String(dump_only=True)

    magic_mimetype = fields.String(dump_only=True)

    storage_type = fields.String(dump_only=True)

    state = fields.String(dump_only=True)

    created_at = fields.DateTime(dump_only=True)

    last_modified = fields.DateTime(dump_only=True)

    creator = fields.Nested(UserSchema, dump_only=True)

    _links = fields.Method("_generate_links")

    _actions = fields.Method("_generate_actions")

    def __init__(self, record=None, previous_file=None, **kwargs):
        super().__init__(**kwargs)

        self.record = record
        self.previous_file = previous_file

    @validates("name")
    def _validate_name(self, value):
        if self.record is not None:
            file = self.record.active_files.filter(File.name == value).first()

            if file is not None and (
                self.previous_file is None or self.previous_file != file
            ):
                raise ValidationError("Name is already in use.")

    @post_dump
    def _post_dump(self, data, **kwargs):
        if "creator" in data and not check_access_token_scopes("user.read"):
            del data["creator"]

        return data

    def _generate_links(self, obj):
        links = {
            "self": url_for("api.get_file", record_id=obj.record_id, file_id=obj.id),
            "download": url_for(
                "api.download_file", record_id=obj.record_id, file_id=obj.id
            ),
            "record": url_for("api.get_record", id=obj.record_id),
            "view": url_for(
                "records.view_file", record_id=obj.record_id, file_id=obj.id
            ),
        }

        # Only include these links if the current user has suitable permissions.
        if self._internal and (
            not has_request_context()
            or (
                current_user.is_authenticated
                and has_permission(current_user, "update", "record", obj.record_id)
            )
        ):
            links["edit_metadata"] = url_for(
                "records.edit_file_metadata", record_id=obj.record_id, file_id=obj.id
            )
            links["edit_data"] = url_for(
                "records.add_files", id=obj.record_id, file=obj.id
            )

        return links

    def _generate_actions(self, obj):
        actions = {
            "delete": url_for(
                "api.delete_file", record_id=obj.record_id, file_id=obj.id
            ),
            "edit_metadata": url_for(
                "api.edit_file_metadata", record_id=obj.record_id, file_id=obj.id
            ),
            "edit_data": url_for(
                "api.edit_file_data", record_id=obj.record_id, file_id=obj.id
            ),
        }

        # If internal, remove this action if the current user does not have suitable
        # permissions.
        if (
            self._internal
            and has_request_context()
            and current_user.is_authenticated
            and not has_permission(current_user, "update", "record", obj.record_id)
        ):
            del actions["delete"]

        return actions


class UploadSchema(BaseSchema):
    """Schema to represent uploads.

    See :class:`.Upload`.
    """

    id = fields.String(dump_only=True)

    name = CustomString(
        required=True,
        filter=normalize,
        validate=Length(max=Upload.Meta.check_constraints["name"]["length"]["max"]),
    )

    size = fields.Integer(
        required=True,
        validate=Range(min=Upload.Meta.check_constraints["size"]["range"]["min"]),
    )

    description = CustomString(
        allow_ws_only=True,
        filter=strip,
        validate=Length(
            max=Upload.Meta.check_constraints["description"]["length"]["max"]
        ),
    )

    mimetype = CustomString(
        filter=[lower, normalize],
        validate=[
            Length(max=Upload.Meta.check_constraints["mimetype"]["length"]["max"]),
            validate_mimetype,
        ],
    )

    checksum = CustomString(
        filter=strip,
        load_default=None,
        validate=Length(max=Upload.Meta.check_constraints["checksum"]["length"]["max"]),
    )

    chunk_count = fields.Integer(dump_only=True)

    storage_type = fields.String(dump_only=True)

    upload_type = fields.String(dump_only=True)

    state = fields.String(dump_only=True)

    created_at = fields.DateTime(dump_only=True)

    last_modified = fields.DateTime(dump_only=True)

    creator = fields.Nested(UserSchema, dump_only=True)

    file = fields.Nested(FileSchema, dump_only=True)

    chunks = fields.Method("_generate_chunks")

    _links = fields.Method("_generate_links")

    _actions = fields.Method("_generate_actions")

    _meta = fields.Method("_generate_meta")

    @post_dump(pass_original=True)
    def _post_dump(self, data, obj, **kwargs):
        if "creator" in data and not check_access_token_scopes("user.read"):
            del data["creator"]

        if "_meta" in data and not data["_meta"]:
            del data["_meta"]

        return data

    def _generate_chunks(self, obj):
        return ChunkSchema(many=True).dump(
            obj.active_chunks.with_entities(Chunk.index, Chunk.size, Chunk.checksum)
        )

    def _generate_links(self, obj):
        return {
            "self": url_for(
                "api.get_upload", record_id=obj.record_id, upload_id=obj.id
            ),
            "record": url_for("api.get_record", id=obj.record_id),
        }

    def _generate_actions(self, obj):
        actions = {
            "delete": url_for(
                "api.delete_upload", record_id=obj.record_id, upload_id=obj.id
            ),
            "upload_data": url_for(
                "api.upload_data", record_id=obj.record_id, upload_id=obj.id
            ),
        }

        if obj.upload_type == UploadType.CHUNKED:
            actions["finish"] = url_for(
                "api.finish_upload", record_id=obj.record_id, upload_id=obj.id
            )

        return actions

    def _generate_meta(self, obj):
        if obj.upload_type == UploadType.CHUNKED:
            chunk_size = const.UPLOAD_CHUNK_SIZE
        else:
            chunk_size = obj.size

        return {"chunk_size": chunk_size}


class ChunkSchema(BaseSchema):
    """Schema to represent chunks.

    See :class:`.Chunk`.

    :param chunk_count: (optional) The total amount of chunks that the upload this chunk
        is part of has. Will be used to validate the chunk's index and size.
    """

    index = fields.Integer(
        required=True,
        validate=Range(min=Chunk.Meta.check_constraints["index"]["range"]["min"]),
    )

    size = fields.Integer(
        required=True,
        validate=Range(min=Chunk.Meta.check_constraints["size"]["range"]["min"]),
    )

    checksum = CustomString(
        filter=strip,
        load_default=None,
        validate=Length(max=Chunk.Meta.check_constraints["checksum"]["length"]["max"]),
    )

    def __init__(self, *args, chunk_count=None, **kwargs):
        self.chunk_count = chunk_count
        super().__init__(*args, **kwargs)

    @validates("index")
    def _validate_index(self, value):
        if self.chunk_count is not None and value >= self.chunk_count:
            raise ValidationError(f"Must be less than {self.chunk_count}.")

    @validates_schema(skip_on_field_errors=False)
    def _validate_schema(self, data, **kwargs):
        if "size" not in data:
            return

        if data["size"] > const.UPLOAD_CHUNK_SIZE:
            raise ValidationError(
                f"Chunk size ({filesize(const.UPLOAD_CHUNK_SIZE)}) exceeded.", "size"
            )

        if (
            self.chunk_count is not None
            and "index" in data
            and data["index"] < self.chunk_count - 1
            and data["size"] < const.UPLOAD_CHUNK_SIZE
        ):
            raise ValidationError(
                "Only the last chunk may be smaller than the chunk size"
                f" ({filesize(const.UPLOAD_CHUNK_SIZE)}).",
                "size",
            )
