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
from kadi.lib.api.utils import status
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import remove_role
from kadi.modules.accounts.models import User
from kadi.modules.groups.core import delete_group as _delete_group
from kadi.modules.groups.models import Group


@bp.delete("/groups/<int:id>")
@permission_required("delete", "group", "id")
@scopes_required("group.delete")
@status(204, "Group successfully marked as deleted.")
def delete_group(id):
    """Mark the group specified by the given ID as deleted.

    Until being removed automatically, a deleted group may be restored or purged using
    the endpoints `POST /api/groups/{id}/restore` or `POST /api/groups/{id}/purge`,
    respectively.
    """
    group = Group.query.get_active_or_404(id)
    _delete_group(group)

    return json_response(204)


@bp.delete("/groups/<int:group_id>/members/<int:user_id>")
@permission_required("members", "group", "group_id")
@scopes_required("group.members")
@status(204, "Member successfully removed from group.")
@status(409, "When trying to remove the creator.")
def remove_group_member(group_id, user_id):
    """Remove a member from a group.

    Will remove the member specified by the given user ID from the group specified by
    the given group ID.
    """
    group = Group.query.get_active_or_404(group_id)
    user = User.query.get_active_or_404(user_id)

    if user.is_merged:
        return json_error_response(404)

    return remove_role(user, group)
