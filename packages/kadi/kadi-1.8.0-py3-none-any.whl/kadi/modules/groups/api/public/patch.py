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
from kadi.ext.db import db
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.api.core import scopes_required
from kadi.lib.api.utils import reqschema
from kadi.lib.api.utils import status
from kadi.lib.permissions.schemas import RoleSchema
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import change_role
from kadi.modules.accounts.models import User
from kadi.modules.groups.core import update_group
from kadi.modules.groups.models import Group
from kadi.modules.groups.schemas import GroupSchema


@bp.patch("/groups/<int:id>")
@permission_required("update", "group", "id")
@scopes_required("group.update")
@reqschema(
    GroupSchema(exclude=["id"], partial=True),
    description="The new metadata of the group.",
    bind=False,
)
@status(200, "Return the updated group.")
@status(409, "A conflict occured while trying to update the group.")
def edit_group(id):
    """Update the group specified by the given ID."""
    group = Group.query.get_active_or_404(id)
    data = GroupSchema(previous_group=group, exclude=["id"], partial=True).load_or_400()

    if not update_group(group, **data):
        return json_error_response(409, description="Error updating group.")

    db.session.commit()

    return json_response(200, GroupSchema().dump(group))


@bp.patch("/groups/<int:group_id>/members/<int:user_id>")
@permission_required("members", "group", "group_id")
@scopes_required("group.members")
@reqschema(RoleSchema, description="The new member.")
@status(204, "Member's role successfully changed.")
@status(
    409,
    "When trying to change the creator's role or a conflict occured while trying to"
    " change the role.",
)
def change_group_member(group_id, user_id, schema):
    """Change a member's role of a group.

    Will change the role of the member specified by the given user ID of the group
    specified by the given group ID.
    """
    group = Group.query.get_active_or_404(group_id)
    user = User.query.get_active_or_404(user_id)

    if user.is_merged:
        return json_error_response(404)

    return change_role(user, group, schema.load_or_400()["name"])
