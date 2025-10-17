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
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.api.core import scopes_required
from kadi.lib.api.utils import reqschema
from kadi.lib.api.utils import status
from kadi.lib.exceptions import KadiPermissionError
from kadi.lib.permissions.schemas import RoleSchema
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import change_role
from kadi.modules.accounts.models import User
from kadi.modules.groups.models import Group
from kadi.modules.records.core import update_record
from kadi.modules.records.files import update_file
from kadi.modules.records.links import update_record_link
from kadi.modules.records.models import File
from kadi.modules.records.models import Record
from kadi.modules.records.models import RecordLink
from kadi.modules.records.schemas import FileSchema
from kadi.modules.records.schemas import RecordLinkSchema
from kadi.modules.records.schemas import RecordSchema


@bp.patch("/records/<int:id>")
@permission_required("update", "record", "id")
@scopes_required("record.update")
@reqschema(
    RecordSchema(exclude=["id"], partial=True),
    description="The new metadata of the record.",
    bind=False,
)
@status(200, "Return the updated record.")
@status(409, "A conflict occured while trying to update the record.")
def edit_record(id):
    """Update the record specified by the given ID."""
    record = Record.query.get_active_or_404(id)
    data = RecordSchema(
        previous_record=record, exclude=["id"], partial=True
    ).load_or_400()

    if not update_record(record, **data):
        return json_error_response(409, description="Error updating record.")

    return json_response(200, RecordSchema().dump(record))


@bp.patch("/records/<int:record_id>/records/<int:link_id>")
@permission_required("link", "record", "record_id")
@scopes_required("record.link")
@reqschema(
    RecordLinkSchema(only=["record_to.id", "name", "term"], partial=True),
    description="The metadata of the new record link.",
)
@status(200, "Return the updated record link.")
@status(409, "The link already exists.")
def edit_record_link(record_id, link_id, schema):
    """Update a record link.

    Will update the outgoing record link specified by the given link ID from the record
    specified by the given record ID.
    """
    record = Record.query.get_active_or_404(record_id)
    record_link = record.links_to.filter(RecordLink.id == link_id).first_or_404()

    data = schema.load_or_400()

    if "record_to" in data:
        if record_to_id := data["record_to"].get("id"):
            data["record_to"] = record_to_id
        else:
            del data["record_to"]

    try:
        update_record_link(record_link, **data)
    except KadiPermissionError as e:
        return json_error_response(403, description=str(e))
    except ValueError as e:
        return json_error_response(409, description=str(e))

    return json_response(
        200, RecordLinkSchema(exclude=["record_from"]).dump(record_link)
    )


@bp.patch("/records/<int:record_id>/roles/users/<int:user_id>")
@permission_required("permissions", "record", "record_id")
@scopes_required("record.permissions")
@reqschema(RoleSchema, description="The new user role.")
@status(204, "User role successfully changed.")
@status(
    409,
    "When trying to change the creator's role or a conflict occured while trying to"
    " change the role.",
)
def change_record_user_role(record_id, user_id, schema):
    """Change a user role of a record.

    Will change the role of the user specified by the given user ID of the record
    specified by the given record ID.
    """
    record = Record.query.get_active_or_404(record_id)
    user = User.query.get_active_or_404(user_id)

    if user.is_merged:
        return json_error_response(404)

    return change_role(user, record, schema.load_or_400()["name"])


@bp.patch("/records/<int:record_id>/roles/groups/<int:group_id>")
@permission_required("permissions", "record", "record_id")
@scopes_required("record.permissions")
@reqschema(RoleSchema, description="The new group role.")
@status(204, "Group role successfully changed.")
@status(409, "A conflict occured while trying to change the role.")
def change_record_group_role(record_id, group_id, schema):
    """Change a group role of a record.

    Will change the role of the group specified by the given group ID of the record
    specified by the given record ID.
    """
    record = Record.query.get_active_or_404(record_id)
    group = Group.query.get_active_or_404(group_id)

    return change_role(group, record, schema.load_or_400()["name"])


@bp.patch("/records/<int:record_id>/files/<uuid:file_id>")
@permission_required("update", "record", "record_id")
@scopes_required("record.update")
@reqschema(
    FileSchema(exclude=["id"], partial=True),
    description="The new metadata of the file.",
    bind=False,
)
@status(200, "Return the updated file.")
@status(409, "A conflict occured while trying to update the file.")
def edit_file_metadata(record_id, file_id):
    """Update the metadata of a file of a record.

    Will update the file specified by the given file ID of the record specified by the
    given record ID.
    """
    record = Record.query.get_active_or_404(record_id)
    file = record.active_files.filter(File.id == file_id).first_or_404()

    data = FileSchema(
        record=record, previous_file=file, exclude=["id"], partial=True
    ).load_or_400()

    if not update_file(file, **data):
        return json_error_response(409, description="Error updating file.")

    return json_response(200, FileSchema().dump(file))
