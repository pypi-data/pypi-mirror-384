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
import math
from mimetypes import guess_type
from uuid import uuid4

from flask import current_app
from flask_babel import lazy_gettext as _l
from sqlalchemy import Column
from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import NestedTransaction
from kadi.lib.db import SimpleTimestampMixin
from kadi.lib.db import StateTimestampMixin
from kadi.lib.db import generate_check_constraints
from kadi.lib.db import unique_constraint
from kadi.lib.favorites.models import FavoriteMixin
from kadi.lib.search.models import SearchableMixin
from kadi.lib.storage.core import get_storage_provider
from kadi.lib.tags.models import TaggingMixin
from kadi.lib.utils import SimpleReprMixin
from kadi.lib.utils import StringEnum

from .extras import ExtrasJSONB


class RecordVisibility(StringEnum):
    """String enum containing all possible visibility values for records.

    * ``PRIVATE``: For records that are not readable without explicit permission.
    * ``PUBLIC``: For records that are readable by all authenticated users.
    """

    __values__ = [const.RESOURCE_VISIBILITY_PRIVATE, const.RESOURCE_VISIBILITY_PUBLIC]


class RecordState(StringEnum):
    """String enum containing all possible state values for records.

    * ``ACTIVE``: For records that are active.
    * ``DELETED``: For records that have been marked for deletion.
    * ``PURGED``: For records that are in the process of being deleted.
    """

    __values__ = [const.MODEL_STATE_ACTIVE, const.MODEL_STATE_DELETED, "purged"]


class Record(
    SimpleReprMixin,
    SearchableMixin,
    StateTimestampMixin,
    FavoriteMixin,
    TaggingMixin,
    db.Model,
):
    """Model to represent records."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "identifier", "visibility", "state"]
        """See :class:`.SimpleReprMixin`."""

        search_mapping = "kadi.modules.records.mappings.RecordMapping"
        """See :class:`.SearchableMixin`."""

        timestamp_exclude = ["uploads", "temporary_files"]
        """See :class:`.BaseTimestampMixin`."""

        revision = [
            "identifier",
            "title",
            "type",
            "description",
            "extras",
            "visibility",
            "state",
            "license[name]",
            "tags[name]",
            "links_to[id, record_to_id, name, term]",
            "linked_from[id, record_from_id, name, term]",
        ]
        """See :func:`kadi.lib.revisions.core.setup_revisions`."""

        permissions = {
            "actions": {
                "create": "Create new records.",
                "read": _l("View this record and its files."),
                "link": _l("Manage links of this record with other resources."),
                "update": _l("Edit this record and its files."),
                "permissions": _l("Manage permissions of this record."),
                "delete": _l("Delete this record."),
            },
            "roles": {
                "member": ["read"],
                "collaborator": ["read", "link"],
                "editor": ["read", "link", "update"],
                "admin": ["read", "link", "update", "permissions", "delete"],
            },
            "default_permissions": {
                "read": {"visibility": RecordVisibility.PUBLIC},
            },
        }
        """Available actions, roles and default permissions for records.

        See :mod:`kadi.lib.permissions`.
        """

        check_constraints = {
            "identifier": {"length": {"max": const.RESOURCE_IDENTIFIER_MAX_LEN}},
            "title": {"length": {"max": const.RESOURCE_TITLE_MAX_LEN}},
            "type": {"length": {"max": 50}},
            "description": {"length": {"max": const.RESOURCE_DESCRIPTION_MAX_LEN}},
            "visibility": {"values": RecordVisibility.__values__},
            "state": {"values": RecordState.__values__},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "record"

    __table_args__ = generate_check_constraints(Meta.check_constraints)

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the record, auto incremented."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` who created the record."""

    identifier = db.Column(db.Text, index=True, unique=True, nullable=False)
    """The unique identifier of the record.

    Restricted to a maximum length of ``50`` characters.
    """

    title = db.Column(db.Text, nullable=False)
    """The title of the record.

    Restricted to a maximum length of ``150`` characters.
    """

    type = db.Column(db.Text, nullable=True)
    """The optional type of the record.

    Restricted to a maximum length of ``50`` characters.
    """

    description = db.Column(db.Text, nullable=False)
    """The description of the record.

    Restricted to a maximum length of ``50_000`` characters.
    """

    plain_description = db.Column(db.Text, nullable=False)
    """The plain description of the record.

    Equal to the normal description with the difference that most markdown is stripped
    out and whitespaces are normalized.
    """

    license_id = db.Column(db.Integer, db.ForeignKey("license.id"), nullable=True)
    """The optional ID of the :class:`.License` of the record."""

    extras = db.Column(ExtrasJSONB, nullable=False)
    """The extra metadata of the record.

    The extras are stored in JSON format as an array of objects, each object
    corresponding to an enhanced key/value-pair representing the metadatum. Each object
    contains some or all of the following properties:

    * **type:** The type of the extra, which is always present and must be one of
      ``"str"``, ``"int"``, ``"float"``, ``"bool"``, ``"date"``, ``"dict"`` or
      ``"list"``. Dictionaries (``"dict"``) and lists (``"list"``) contain nested values
      of the same structure as the top level extra metadata values (i.e. an array of
      objects), the only difference being that ``"list"`` values have no keys. All other
      types contain literal values of the corresponding type:

      * ``"str"``: A (non-empty) string value.
      * ``"int"``: An integer value. Limited to values between ``-(2^53 - 1)`` and
        ``2^53 - 1``.
      * ``"float"``: A float value using double-precision (64 Bit) floating point
        format.
      * ``"bool"``: A (binary) boolean value, either ``true`` or ``false``.
      * ``"date"``: A date and time string value according to ISO 8601 format.

    * **key:** The key of the extra as string, which needs to be unique within each
      array. Except for ``"list"`` values, it always needs to be present.
    * **value:** The value of the extra depending on its type. Defaults to ``null`` for
      literal values and an empty array for nested types.
    * **unit:** A unit the value corresponds to as string. Only usable in combination
      with the ``"int"`` or ``"float"`` type. Defaults to ``null``.
    * **description:** An optional description of the extra as string.
    * **term:** An optional IRI (Internationalized Resource Identifier) as string, which
      can be used to specify an existing term that the extra should represent.
    * **validation:** An optional object containing additional, also optional,
      validation instructions for the values of non-nested types. The following
      instructions are currently supported:

      * **required:** A boolean value indicating whether the value of the extra should
        be required, i.e. not ``null``.
      * **options:** An array containing an enumeration of (distinct) possible values
        that the extra can have, which all need to match the type of the extra. Only
        usable in combination with the ``"str"``, ``"int"`` or ``"float"`` type.
      * **range:** An object containing a maximum (``"max"``) and minimum (``"min"``)
        value to restrict the range of the value an extra can have. Each range value may
        also be ``null``, in which case the values are only limited in one direction.
        Note that the range is always inclusive. Only usable in combination with the
        ``"int"`` or ``"float"`` type.
      * **iri:** A boolean value indicating whether the value of the extra represents an
        IRI. Only usable in combination with the ``"str"`` type.
    """

    visibility = db.Column(db.Text, index=True, nullable=False)
    """The default visibility of the record.

    See :class:`.RecordVisibility`.
    """

    state = db.Column(db.Text, index=True, nullable=False)
    """The state of the record.

    See :class:`.RecordState`.
    """

    creator = db.relationship("User", back_populates="records")

    license = db.relationship("License", back_populates="records")

    files = db.relationship("File", lazy="dynamic", back_populates="record")

    uploads = db.relationship("Upload", lazy="dynamic", back_populates="record")

    temporary_files = db.relationship(
        "TemporaryFile",
        lazy="dynamic",
        back_populates="record",
        cascade="all, delete-orphan",
    )

    tags = db.relationship(
        "Tag", secondary="record_tag", lazy="dynamic", back_populates="records"
    )

    collections = db.relationship(
        "Collection",
        secondary="record_collection",
        lazy="dynamic",
        back_populates="records",
    )

    links_to = db.relationship(
        "RecordLink",
        lazy="dynamic",
        back_populates="record_from",
        foreign_keys="RecordLink.record_from_id",
        cascade="all, delete-orphan",
    )

    linked_from = db.relationship(
        "RecordLink",
        lazy="dynamic",
        back_populates="record_to",
        foreign_keys="RecordLink.record_to_id",
        cascade="all, delete-orphan",
    )

    @property
    def active_files(self):
        """Get all active files of a record as a query."""
        return self.files.filter(File.state == FileState.ACTIVE)

    @classmethod
    def create(
        cls,
        *,
        creator,
        identifier,
        title,
        type=None,
        description="",
        plain_description="",
        license=None,
        extras=None,
        visibility=RecordVisibility.PRIVATE,
        state=RecordState.ACTIVE,
    ):
        """Create a new record and add it to the database session.

        :param creator: The creator of the record.
        :param identifier: The unique identifier of the record.
        :param title: The title of the record.
        :param type: (optional) The type of the record.
        :param description: (optional) The description of the record.
        :param plain_description: (optional) The plain description of the record.
        :param license: (optional) The license of the record.
        :param extras: (optional) The extra metadata of the record.
        :param visibility: (optional) The default visibility of the record.
        :param state: (optional) The state of the record.
        :return: The new :class:`Record` object.
        """
        extras = extras if extras is not None else []

        record = cls(
            creator=creator,
            identifier=identifier,
            title=title,
            type=type,
            description=description,
            plain_description=plain_description,
            license=license,
            extras=extras,
            visibility=visibility,
            state=state,
        )
        db.session.add(record)

        return record


class RecordLink(SimpleReprMixin, SimpleTimestampMixin, db.Model):
    """Model to represent directional links between records."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "name", "record_from_id", "record_to_id"]
        """See :class:`.SimpleReprMixin`."""

        check_constraints = {
            "name": {"length": {"max": 150}},
            "term": {"length": {"max": 2_048}},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "record_link"

    __table_args__ = generate_check_constraints(Meta.check_constraints)

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the link, auto incremented."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` who created the record link."""

    name = db.Column(db.Text, nullable=False)
    """The name of the link.

    Restricted to a maximum length of ``150`` characters.
    """

    term = db.Column(db.Text, nullable=True)
    """An optional IRI of an existing term that the link should represent.

    Restricted to a maximum length of ``2_048`` characters.
    """

    record_from_id = db.Column(db.Integer, db.ForeignKey("record.id"), nullable=False)
    """The ID of the :class:`.Record` the link points from."""

    record_to_id = db.Column(db.Integer, db.ForeignKey("record.id"), nullable=False)
    """The ID of the :class:`.Record` the link points to."""

    creator = db.relationship("User", back_populates="record_links")

    record_from = db.relationship(
        "Record", foreign_keys=record_from_id, back_populates="links_to"
    )

    record_to = db.relationship(
        "Record", foreign_keys=record_to_id, back_populates="linked_from"
    )

    @classmethod
    def create(cls, *, creator, name, record_from, record_to, term=None):
        """Create a new record link and add it to the database session.

        :param creator: The creator of the record link.
        :param name: The name of the link.
        :param record_from: The record the link points from.
        :param record_to: The record the link points to.
        :param term: (optional) The term the record link should represent.
        :return: The new :class:`RecordLink` object.
        """
        record_link = cls(
            creator=creator,
            name=name,
            record_from=record_from,
            record_to=record_to,
            term=term,
        )
        db.session.add(record_link)

        return record_link


class FileState(StringEnum):
    """String enum containing all possible state values for files.

    * ``ACTIVE``: For files that are active.
    * ``INACTIVE``: For files that have been marked for deletion of their corresponding
      data.
    * ``DELETED``: For files that have no corresponding data anymore.
    """

    __values__ = [const.MODEL_STATE_ACTIVE, "inactive", const.MODEL_STATE_DELETED]


class File(SimpleReprMixin, StateTimestampMixin, db.Model):
    """Model to represent files."""

    class Meta:
        """Container to store meta class attributes."""

        representation = [
            "id",
            "user_id",
            "record_id",
            "name",
            "size",
            "mimetype",
            "storage_type",
            "state",
        ]
        """See :class:`.SimpleReprMixin`."""

        timestamp_exclude = ["storage_type", "uploads"]
        """See :class:`.BaseTimestampMixin`."""

        revision = ["name", "description", "size", "mimetype", "checksum", "state"]
        """See :func:`kadi.lib.revisions.core.setup_revisions`."""

        check_constraints = {
            "name": {"length": {"max": 256}},
            "description": {"length": {"max": 50_000}},
            "size": {"range": {"min": 0}},
            "checksum": {"length": {"max": 256}},
            "mimetype": {"length": {"max": 256}},
            "state": {"values": FileState.__values__},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "file"

    __table_args__ = (
        *generate_check_constraints(Meta.check_constraints),
        Index(
            "uq_file_record_id_name",
            "record_id",
            "name",
            unique=True,
            postgresql_where=Column("state") == FileState.ACTIVE,
        ),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    """The UUID of the file."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` who created the file."""

    record_id = db.Column(db.Integer, db.ForeignKey("record.id"), nullable=False)
    """The ID of the :class:`.Record` the file belongs to."""

    name = db.Column(db.Text, nullable=False)
    """The name of the file.

    Restricted to a maximum length of ``256`` characters.
    """

    description = db.Column(db.Text, nullable=False)
    """The description of the file.

    Restricted to a maximum length of ``50_000`` characters.
    """

    size = db.Column(db.BigInteger, nullable=False)
    """The size of the file in bytes.

    Must be a value greater than or equal to ``0``.
    """

    checksum = db.Column(db.Text, nullable=True)
    """The checksum of the file.

    The actual value depends on how a file was uploaded. For direct uploads, the value
    is an MD5 hash of the file's content. For chunked uploads, the value is an MD5 hash
    created by first concatenating the MD5 hashes of all uploaded chunks (in chunk index
    order) and then calculating an MD5 hash of the result. The amount of chunks is then
    appended to the resulting value in the form of ``"<hash>-<chunk_count>"``.

    Restricted to a maximum length of ``256`` characters.
    """

    mimetype = db.Column(db.Text, nullable=False)
    """Regular MIME type of the file, possibly user-provided.

    Restricted to a maximum length of ``256`` characters.
    """

    magic_mimetype = db.Column(db.Text, nullable=True)
    """MIME type based on magic numbers in the file's content."""

    storage_type = db.Column(db.Text, nullable=False)
    """The storage provider type of the file."""

    state = db.Column(db.Text, index=True, nullable=False)
    """The state of the file.

    See :class:`.FileState`.
    """

    creator = db.relationship("User", back_populates="files")

    record = db.relationship("Record", back_populates="files")

    uploads = db.relationship("Upload", lazy="dynamic", back_populates="file")

    @property
    def identifier(self):
        """The identifier of the file.

        Mainly used in correspondence with the file's storage provider.
        """
        return str(self.id)

    @property
    def storage(self):
        """Get the storage provider of this file."""
        return get_storage_provider(self.storage_type)

    @property
    def has_md5_checksum(self):
        """Check if the checksum of this file is an MD5 hash of it's content."""
        if self.checksum is None:
            return False

        # The dash means that the file was created via a chunked upload.
        return "-" not in self.checksum

    @classmethod
    def create(
        cls,
        *,
        creator,
        record,
        name,
        size,
        description="",
        checksum=None,
        mimetype=const.MIMETYPE_BINARY,
        magic_mimetype=None,
        storage_type=None,
        state=FileState.INACTIVE,
    ):
        """Create a new file and add it to the database session.

        :param creator: The creator of the file.
        :param record: The record the file belongs to.
        :param name: The name of the file.
        :param size: The size of the file in bytes.
        :param description: (optional) The description of the file.
        :param checksum: (optional) The checksum of the file.
        :param mimetype: (optional) The regular MIME type of the file.
        :param magic_mimetype: (optional) The MIME type of the file based on its
            content.
        :param storage_type: (optional) The storage provider type of the file. Defaults
            to the ``STORAGE_PROVIDER`` specified in the application's configuration.
        :param state: (optional) The state of the file.
        :return: The new :class:`File` object.
        """
        if storage_type is None:
            storage_type = current_app.config["STORAGE_PROVIDER"]

        file = cls(
            creator=creator,
            record=record,
            name=name,
            size=size,
            description=description,
            checksum=checksum,
            mimetype=mimetype,
            magic_mimetype=magic_mimetype,
            storage_type=storage_type,
            state=state,
        )
        db.session.add(file)

        return file


class UploadType(StringEnum):
    """String enum containing all currently used upload type values for uploads.

    * ``DIRECT``: For smaller uploads that require uploading all data at once after
      initialization.
    * ``CHUNKED``: For larger uploads that require uploading data in fixed chunks. Once
      uploaded, the upload has to be finished explicitely, which will trigger a merge of
      all data chunks.
    """

    __values__ = ["direct", "chunked"]


class UploadState(StringEnum):
    """String enum containing all possible state values for uploads.

    * ``ACTIVE``: For uploads that have been initialized and are ready for uploading
      data or data chunks.
    * ``PROCESSING``: For direct uploads for which data is currently being uploaded or
      chunked uploads which are in the process of being merged.
    * ``INACTIVE``: For uploads that have been completed, either successfully or with an
      error, and uploads that have been marked for deletion.
    """

    __values__ = [const.MODEL_STATE_ACTIVE, "processing", "inactive"]


class Upload(SimpleReprMixin, StateTimestampMixin, db.Model):
    """Model to represent uploads."""

    class Meta:
        """Container to store meta class attributes."""

        representation = [
            "id",
            "user_id",
            "record_id",
            "file_id",
            "name",
            "size",
            "storage_type",
            "upload_type",
            "state",
        ]
        """See :class:`.SimpleReprMixin`."""

        timestamp_exclude = ["storage_type"]
        """See :class:`.BaseTimestampMixin`."""

        check_constraints = {
            "name": {"length": {"max": 256}},
            "size": {"range": {"min": 0}},
            "checksum": {"length": {"max": 256}},
            "description": {"length": {"max": 50_000}},
            "mimetype": {"length": {"max": 256}},
            "chunk_count": {"range": {"min": 1}},
            "upload_type": {"values": UploadType.__values__},
            "state": {"values": UploadState.__values__},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "upload"

    __table_args__ = generate_check_constraints(Meta.check_constraints)

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    """The UUID of the upload."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` who initiated the upload."""

    record_id = db.Column(db.Integer, db.ForeignKey("record.id"), nullable=False)
    """The ID of the :class:`.Record` the upload belongs to."""

    file_id = db.Column(UUID(as_uuid=True), db.ForeignKey("file.id"), nullable=True)
    """The optional ID of a :class:`.File` to be overwritten by the upload."""

    name = db.Column(db.Text, nullable=False)
    """The name of the upload.

    Restricted to a maximum length of ``256`` characters.
    """

    size = db.Column(db.BigInteger, nullable=False)
    """The size of the upload in bytes.

    Must be a value greater than or equal to ``0``.
    """

    checksum = db.Column(db.Text, nullable=True)
    """The checksum of the upload.

    Calculated automatically during the upload process. The actual value depends on the
    upload type and is copied to the resulting file, see :attr:`File.checksum`.

    Restricted to a maximum length of ``256`` characters.
    """

    description = db.Column(db.Text, nullable=True)
    """The optional description of the upload.

    Restricted to a maximum length of ``50_000`` characters.
    """

    mimetype = db.Column(db.Text, nullable=True)
    """The optional MIME type of the upload.

    Restricted to a maximum length of ``256`` characters.
    """

    chunk_count = db.Column(db.Integer, nullable=False)
    """Number of chunks an upload is split into.

    For direct uploads, the chunk count is always ``1``.

    Must be a value greater than or equal to ``1``.
    """

    storage_type = db.Column(db.Text, nullable=False)
    """The storage provider type of the upload."""

    upload_type = db.Column(db.Text, nullable=False)
    """The type of the upload.

    See :class:`.UploadType`.
    """

    state = db.Column(db.Text, index=True, nullable=False)
    """The state of the upload.

    See :class:`.UploadState`.
    """

    creator = db.relationship("User", back_populates="uploads")

    record = db.relationship("Record", back_populates="uploads")

    file = db.relationship("File", back_populates="uploads")

    chunks = db.relationship("Chunk", lazy="dynamic", back_populates="upload")

    @property
    def identifier(self):
        """The identifier of the upload.

        Mainly used in correspondence with the upload's storage provider.
        """
        return str(self.id)

    @property
    def storage(self):
        """Get the storage provider of this upload."""
        return get_storage_provider(self.storage_type)

    @property
    def active_chunks(self):
        """Get all active chunks of this upload as query."""
        return self.chunks.filter(Chunk.state == ChunkState.ACTIVE)

    @classmethod
    def create(
        cls,
        *,
        creator,
        record,
        name,
        size,
        description=None,
        mimetype=None,
        chunk_count=None,
        storage_type=None,
        upload_type=None,
        file=None,
        state=UploadState.ACTIVE,
    ):
        """Create a new upload and add it to the database session.

        :param creator: The user who is initiating the upload.
        :param record: The record the upload belongs to.
        :param name: The name of the upload.
        :param size: The size of the upload in bytes.
        :param description: (optional) The description of the upload.
        :param mimetype: (optional) The MIME type of the upload.
        :param chunk_count: (optional) The chunk count of the upload. Defaults to an
            automatically calculated value based on
            :const:`kadi.lib.constants.UPLOAD_CHUNK_SIZE` for chunked uploads, and to
            ``1`` for direct uploads.
        :param storage_type: (optional) The storage provider type of the upload.
            Defaults to the ``STORAGE_PROVIDER`` specified in the application's
            configuration.
        :param upload_type: (optional) The upload type. Defaults to a type based on the
            provided size and :const:`kadi.lib.constants.UPLOAD_CHUNKED_BOUNDARY`.
        :param file: (optional) A file the upload should replace.
        :param state: The state of the upload.
        :return: The new :class:`Upload` object.
        """
        if storage_type is None:
            storage_type = current_app.config["STORAGE_PROVIDER"]

        if upload_type is None:
            if size > const.UPLOAD_CHUNKED_BOUNDARY:
                upload_type = UploadType.CHUNKED
            else:
                upload_type = UploadType.DIRECT

        if chunk_count is None:
            if upload_type == UploadType.CHUNKED:
                chunk_count = (
                    math.ceil(size / const.UPLOAD_CHUNK_SIZE) if size > 0 else 1
                )
            else:
                chunk_count = 1

        upload = cls(
            record=record,
            creator=creator,
            name=name,
            size=size,
            chunk_count=chunk_count,
            description=description,
            mimetype=mimetype,
            storage_type=storage_type,
            upload_type=upload_type,
            file=file,
            state=state,
        )
        db.session.add(upload)

        return upload


class ChunkState(StringEnum):
    """String enum containing all possible state values for chunks.

    * ``ACTIVE``: For chunks that are active and ready to be merged.
    * ``INACTIVE``: For chunks that are inactive.
    """

    __values__ = [const.MODEL_STATE_ACTIVE, "inactive"]


class Chunk(SimpleReprMixin, db.Model):
    """Model to represent file chunks."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "upload_id", "index", "size", "state"]
        """See :class:`.SimpleReprMixin`."""

        check_constraints = {
            "index": {"range": {"min": 0}},
            "size": {"range": {"min": 0}},
            "checksum": {"length": {"max": 256}},
            "state": {"values": ChunkState.__values__},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "chunk"

    __table_args__ = (
        *generate_check_constraints(Meta.check_constraints),
        unique_constraint(__tablename__, "upload_id", "index"),
    )

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the chunk, auto incremented."""

    upload_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("upload.id"), nullable=False
    )
    """The ID of the :class:`.Upload` the chunk belongs to."""

    index = db.Column(db.Integer, nullable=False)
    """The index of the chunk inside its upload.

    Must be a value greater than or equal to ``0``.
    """

    size = db.Column(db.Integer, nullable=False)
    """The size of the chunk in bytes.

    Must be a value greater than or equal to ``0``.
    """

    checksum = db.Column(db.Text, nullable=True)
    """The checksum of the chunk.

    Always corresponds to an MD5 hash of the chunk's content, which is calculated
    automatically during the chunk upload process.

    Restricted to a maximum length of ``256`` characters.
    """

    state = db.Column(db.Text, index=True, nullable=False)
    """The state of the chunk.

    See :class:`.ChunkState`.
    """

    upload = db.relationship("Upload", back_populates="chunks")

    @property
    def identifier(self):
        """The identifier of the chunk.

        Mainly used in correspondence with the storage provider of the chunk's upload.
        """
        return f"{self.upload_id}-{self.index}"

    @classmethod
    def create(cls, *, upload, index, size, state=ChunkState.INACTIVE):
        """Create a new chunk and add it to the database session.

        :param upload: The upload the chunk belongs to.
        :param index: The index of the chunk.
        :param size: The size of the chunk in bytes.
        :param state: (optional) The state of the chunk.
        :return: The new :class:`Chunk` object.
        """
        chunk = cls(upload=upload, index=index, size=size, state=state)
        db.session.add(chunk)

        return chunk

    @classmethod
    def update_or_create(cls, *, upload, index, size, state=ChunkState.INACTIVE):
        """Update an existing chunk or create one if it does not exist yet.

        See :meth:`create` for an explanation of the parameters.

        :return: The new or updated :class:`.Chunk` object.
        """
        chunk_query = cls.query.filter_by(upload=upload, index=index)
        chunk = chunk_query.first()

        if not chunk:
            with NestedTransaction(exc=IntegrityError) as t:
                chunk = cls.create(upload=upload, index=index, size=size, state=state)

            if not t.success:
                chunk = chunk_query.first()

        chunk.size = size
        chunk.state = state

        return chunk


class TemporaryFileState(StringEnum):
    """String enum containing all possible state values for temporary files."""

    __values__ = [const.MODEL_STATE_ACTIVE, "inactive"]


class TemporaryFile(SimpleReprMixin, StateTimestampMixin, db.Model):
    """Model to represent temporary files.

    Currently not used anymore, but may still be repurposed in the future.
    """

    class Meta:
        """Container to store meta class attributes."""

        representation = [
            "id",
            "user_id",
            "record_id",
            "type",
            "name",
            "size",
            "mimetype",
            "state",
        ]
        """See :class:`.SimpleReprMixin`."""

        check_constraints = {
            "name": {"length": {"max": 256}},
            "size": {"range": {"min": 0}},
            "mimetype": {"length": {"max": 256}},
            "state": {"values": TemporaryFileState.__values__},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "temporary_file"

    __table_args__ = generate_check_constraints(Meta.check_constraints)

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    """The UUID of the temporary file."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` who created the temporary file."""

    record_id = db.Column(db.Integer, db.ForeignKey("record.id"), nullable=False)
    """The ID of the :class:`.Record` the temporary file belongs to."""

    type = db.Column(db.Text, nullable=True)
    """The optional type of the temporary file.

    Can be used to distinguish different types of temporary files for different use
    cases.
    """

    name = db.Column(db.Text, nullable=False)
    """The name of the temporary file.

    Restricted to a maximum length of ``256`` characters.
    """

    size = db.Column(db.BigInteger, nullable=False)
    """The size of the temporary file in bytes.

    Must be a value greater than or equal to ``0``.
    """

    mimetype = db.Column(db.Text, nullable=False)
    """MIME type of the temporary file.

    Restricted to a maximum length of ``256`` characters.
    """

    state = db.Column(db.Text, index=True, nullable=False)
    """The state of the temporary file.

    See :class:`.TemporaryFileState`.
    """

    creator = db.relationship("User", back_populates="temporary_files")

    record = db.relationship("Record", back_populates="temporary_files")

    @classmethod
    def create(
        cls,
        *,
        creator,
        record,
        name,
        size,
        type=None,
        mimetype=None,
        state=TemporaryFileState.INACTIVE,
    ):
        """Create a new temporary file and add it to the database session.

        :param creator: The creator of the temporary file.
        :param record: The record the temporary file belongs to.
        :param name: The name of the temporary file.
        :param size: The size of the temporary file in bytes.
        :param type: (optional) The type of the temporary file.
        :param mimetype: (optional) The MIME type of the temporary file. Defaults to a
            MIME type based on the filename or the default MIME type as defined in
            :const:`kadi.lib.constants.MIMETYPE_BINARY` if it cannot be guessed.
        :param state: (optional) The state of the temporary file.
        :return: The new :class:`TemporaryFile` object.
        """
        if mimetype is None:
            mimetype = guess_type(name)[0] or const.MIMETYPE_BINARY

        temporary_file = cls(
            creator=creator,
            record=record,
            name=name,
            size=size,
            type=type,
            mimetype=mimetype,
            state=state,
        )
        db.session.add(temporary_file)

        return temporary_file


# Auxiliary table to link records with collections.
db.Table(
    "record_collection",
    db.Column("record_id", db.Integer, db.ForeignKey("record.id"), primary_key=True),
    db.Column(
        "collection_id", db.Integer, db.ForeignKey("collection.id"), primary_key=True
    ),
)


# Auxiliary table for record tags.
db.Table(
    "record_tag",
    db.Column("record_id", db.Integer, db.ForeignKey("record.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)
