# Copyright 2021 Karlsruhe Institute of Technology
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
from kadi.lib.api.core import internal
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.permissions.core import remove_role_rule
from kadi.lib.permissions.models import RoleRule
from kadi.lib.permissions.utils import permission_required
from kadi.modules.groups.models import Group


@bp.delete("/groups/<int:group_id>/rules/<int:rule_id>")
@permission_required("members", "group", "group_id")
@internal
def remove_group_role_rule(group_id, rule_id):
    """Remove a role rule of a group."""
    group = Group.query.get_active_or_404(group_id)
    role_rule = RoleRule.query.get_or_404(rule_id)

    role = role_rule.role

    if role.object != "group" or role.object_id != group.id:
        return json_error_response(404)

    remove_role_rule(role_rule)
    db.session.commit()

    return json_response(204)
