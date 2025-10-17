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
from flask import current_app
from flask_babel import gettext as _
from flask_login import current_user
from flask_login import login_required

from kadi.ext.db import db
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.api.core import scopes_required
from kadi.lib.api.utils import reqschema
from kadi.lib.api.utils import status
from kadi.lib.exceptions import KadiPermissionError
from kadi.lib.format import filesize
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import add_link
from kadi.lib.resources.api import add_role
from kadi.lib.resources.schemas import GroupResourceRoleSchema
from kadi.lib.resources.schemas import UserResourceRoleSchema
from kadi.modules.accounts.models import User
from kadi.modules.collections.models import Collection
from kadi.modules.collections.schemas import CollectionSchema
from kadi.modules.groups.models import Group
from kadi.modules.records.core import create_record
from kadi.modules.records.core import restore_record as _restore_record
from kadi.modules.records.links import create_record_link
from kadi.modules.records.models import File
from kadi.modules.records.models import Record
from kadi.modules.records.models import RecordState
from kadi.modules.records.models import Upload
from kadi.modules.records.models import UploadState
from kadi.modules.records.models import UploadType
from kadi.modules.records.schemas import FileSchema
from kadi.modules.records.schemas import RecordLinkSchema
from kadi.modules.records.schemas import RecordSchema
from kadi.modules.records.schemas import UploadSchema
from kadi.modules.records.tasks import start_merge_chunks_task
from kadi.modules.records.tasks import start_purge_record_task
from kadi.modules.records.uploads import delete_upload
from kadi.modules.records.utils import get_user_quota


@bp.post("/records")
@permission_required("create", "record", None)
@scopes_required("record.create")
@reqschema(RecordSchema(exclude=["id"]), description="The metadata of the new record.")
@status(201, "Return the new record.")
@status(409, "A conflict occured while trying to create the record.")
def new_record(schema):
    """Create a new record."""
    record = create_record(**schema.load_or_400())

    if not record:
        return json_error_response(409, description="Error creating record.")

    return json_response(201, RecordSchema().dump(record))


@bp.post("/records/<int:id>/records")
@permission_required("link", "record", "id")
@scopes_required("record.link")
@reqschema(
    RecordLinkSchema(only=["name", "term", "record_to.id"]),
    description="The metadata of the new record link.",
)
@status(201, "Return the new record link.")
@status(
    409,
    "When trying to link the record with itself or the link already exists.",
)
def new_record_link(id, schema):
    """Create a new record link.

    Will create a new outgoing record link from the record specified by the given ID.
    """
    record = Record.query.get_active_or_404(id)
    data = schema.load_or_400()
    linked_record = Record.query.get_active_or_404(data.pop("record_to")["id"])

    try:
        record_link = create_record_link(
            record_from=record, record_to=linked_record, **data
        )
    except KadiPermissionError as e:
        return json_error_response(403, description=str(e))
    except ValueError as e:
        return json_error_response(409, description=str(e))

    return json_response(
        201, RecordLinkSchema(exclude=["record_from"]).dump(record_link)
    )


@bp.post("/records/<int:id>/collections")
@permission_required("link", "record", "id")
@scopes_required("record.link")
@reqschema(
    CollectionSchema(only=["id"]), description="The collection to add the record to."
)
@status(201, "Record successfully added to collection.")
@status(409, "The link already exists.")
def add_record_collection(id, schema):
    """Add the record specified by the given ID to a collection."""
    record = Record.query.get_active_or_404(id)
    collection = Collection.query.get_active_or_404(schema.load_or_400()["id"])

    return add_link(record.collections, collection)


@bp.post("/records/<int:id>/roles/users")
@permission_required("permissions", "record", "id")
@scopes_required("record.permissions")
@reqschema(
    UserResourceRoleSchema(only=["user.id", "role.name"]),
    description="The user and corresponding role to add.",
)
@status(201, "User role successfully added to record.")
@status(409, "A role for that user already exists.")
def add_record_user_role(id, schema):
    """Add a user role to the record specified by the given ID."""
    record = Record.query.get_active_or_404(id)
    data = schema.load_or_400()
    user = User.query.get_active_or_404(data["user"]["id"])

    if user.is_merged:
        return json_error_response(404)

    return add_role(user, record, data["role"]["name"])


@bp.post("/records/<int:id>/roles/groups")
@permission_required("permissions", "record", "id")
@scopes_required("record.permissions")
@reqschema(
    GroupResourceRoleSchema(only=["group.id", "role.name"]),
    description="The group and corresponding role to add.",
)
@status(201, "Group role successfully added to record.")
@status(409, "A role for that group already exists.")
def add_record_group_role(id, schema):
    """Add a group role to the record specified by the given ID."""
    record = Record.query.get_active_or_404(id)
    data = schema.load_or_400()
    group = Group.query.get_active_or_404(data["group"]["id"])

    return add_role(group, record, data["role"]["name"])


@bp.post("/records/<int:id>/restore")
@login_required
@scopes_required("misc.manage_trash")
@status(200, "Return the restored record.")
def restore_record(id):
    """Restore the deleted record specified by the given ID.

    Only the creator of a record can restore it.
    """
    record = Record.query.get_or_404(id)

    if record.state != RecordState.DELETED or record.creator != current_user:
        return json_error_response(404)

    _restore_record(record)

    return json_response(200, RecordSchema().dump(record))


@bp.post("/records/<int:id>/purge")
@login_required
@scopes_required("misc.manage_trash")
@status(202, "The purge record task was started successfully.")
@status(
    503,
    "The purge record task could not be started. The record will remain deleted in this"
    " case.",
)
def purge_record(id):
    """Purge the deleted record specified by the given ID.

    Will remove the record permanently, including all of its files. The actual deletion
    process will happen in a background task. Only the creator of a record can purge it.
    """
    record = Record.query.get_or_404(id)

    if record.state != RecordState.DELETED or record.creator != current_user:
        return json_error_response(404)

    # In case it takes longer to actually purge the record, this way it will not show up
    # as a deleted resource anymore and will not be picked up by the periodic cleanup
    # task.
    record.state = RecordState.PURGED
    db.session.commit()

    if not start_purge_record_task(record):
        record.state = RecordState.DELETED
        db.session.commit()

        return json_error_response(503, description="Error starting purge record task.")

    return json_response(202)


@bp.post("/records/<int:id>/uploads")
@permission_required("update", "record", "id")
@scopes_required("record.update")
@reqschema(
    UploadSchema(exclude=["checksum"]), description="The metadata of the new upload."
)
@status(201, "Return the new upload.")
@status(
    409,
    "A file with the name of the upload already exists. The file will be returned as"
    " part of the error response as the `file` property and can be updated using the"
    " endpoint `PUT /api/records/{record_id}/files/{file_id}`, which is also returned"
    " as the `_actions.edit_data` property of the returned file.",
)
@status(413, "The user's upload quota was exceeded.")
def new_upload(id, schema):
    """Upload a new file to the record specified by the given ID.

    This endpoint will initiate a new upload with the given metadata. The corresponding
    file data has to be uploaded separately, either directly or via multiple file
    chunks, depending on the size of the upload. Which method to choose will be
    indicated by the `upload_type` property of the returned upload, being either one of
    `"direct"` or `"chunked"`.

    For both upload types, the endpoint `PUT
    /api/records/{record_id}/uploads/{upload_id}` is used to upload the file data, which
    is also returned as the `_actions.upload_data` property of the returned upload. The
    required size for uploading chunks (except for the final chunk for chunked uploads)
    is returned as the `_meta.chunk_size` property of the returned upload. For direct
    uploads, the chunk size is always equal to the total upload size.
    """
    record = Record.query.get_active_or_404(id)
    data = schema.load_or_400()

    file = record.active_files.filter(File.name == data["name"]).first()

    if file is not None:
        return json_error_response(
            409,
            description=_("A file with that name already exists."),
            file=FileSchema().dump(file),
        )

    upload = Upload.create(creator=current_user, record=record, **data)
    db.session.commit()

    max_quota = current_app.config["UPLOAD_USER_QUOTA"]

    if max_quota is not None and get_user_quota() > max_quota:
        delete_upload(upload)
        db.session.commit()

        return json_error_response(
            413,
            description=_(
                "Maximum upload quota exceeded (%(filesize)s).",
                filesize=filesize(max_quota),
            ),
        )

    return json_response(201, schema.dump(upload))


@bp.post("/records/<int:record_id>/uploads/<uuid:upload_id>")
@permission_required("update", "record", "record_id")
@scopes_required("record.update")
@status(
    202,
    "The upload processing task was started successfully. Also return the updated"
    " upload.",
)
@status(
    503,
    "The upload processing task could not be started. The upload will remain active in"
    " this case.",
)
def finish_upload(record_id, upload_id):
    """Finish a chunked upload.

    Will finish the chunked upload specified by the given upload ID of the record
    specified by the given record ID. Only uploads owned by the current user can be
    finished.

    The upload will be finished by starting an upload processing task to finalize it.
    The status of this task can be queried using the endpoint
    `GET /api/records/{record_id}/uploads/{upload_id}`, which is also returned as the
    `_links.self` property of the returned upload.
    """
    record = Record.query.get_active_or_404(record_id)
    upload = record.uploads.filter(
        Upload.id == upload_id,
        Upload.user_id == current_user.id,
        Upload.state == UploadState.ACTIVE,
        Upload.upload_type == UploadType.CHUNKED,
    ).first_or_404()

    # Perform a basic check whether at least the amount of uploaded chunks matches what
    # is expected.
    if upload.active_chunks.count() != upload.chunk_count:
        return json_error_response(
            400,
            description="Number of uploaded chunks does not match the expected chunk"
            " count.",
        )

    upload.state = UploadState.PROCESSING
    db.session.commit()

    if not start_merge_chunks_task(upload):
        upload.state = UploadState.ACTIVE
        db.session.commit()

        return json_error_response(
            503, description="Error starting upload processing task."
        )

    return json_response(202, UploadSchema().dump(upload))
