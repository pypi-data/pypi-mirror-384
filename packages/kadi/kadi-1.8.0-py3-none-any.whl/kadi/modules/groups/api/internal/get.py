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
from flask_login import current_user
from flask_login import login_required

import kadi.lib.constants as const
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import internal
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.api.utils import create_pagination_data
from kadi.lib.conversion import normalize
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.models import RoleRule
from kadi.lib.permissions.schemas import RoleRuleSchema
from kadi.lib.permissions.utils import get_group_roles
from kadi.lib.permissions.utils import get_role_rules
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import get_selected_resources
from kadi.lib.storage.misc import preview_thumbnail
from kadi.lib.utils import get_class_by_name
from kadi.lib.web import paginated
from kadi.lib.web import qparam
from kadi.modules.groups.models import Group


@bp.get("/groups/<int:id>/image")
@permission_required("read", "group", "id")
@internal
def preview_group_image(id):
    """Preview a group's profile image directly in the browser."""
    group = Group.query.get_active_or_404(id)

    if group.image_name:
        return preview_thumbnail(str(group.image_name), "group.jpg")

    return json_error_response(404)


@bp.get("/groups/<int:id>/rules")
@permission_required("members", "group", "id")
@internal
@paginated
def get_group_role_rules(id, page, per_page):
    """Get role rules of a group."""
    group = Group.query.get_active_or_404(id)
    role_rules = (
        get_role_rules("group", group.id)
        .order_by(RoleRule.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    data = {
        "items": RoleRuleSchema(many=True).dump(role_rules),
        **create_pagination_data(role_rules.total, page, per_page, id=group.id),
    }
    return json_response(200, data)


@bp.get("/groups/select")
@login_required
@internal
@qparam("page", type=const.QPARAM_TYPE_INT, default=1)
@qparam("term", parse=normalize)
@qparam("exclude", type=const.QPARAM_TYPE_INT, multiple=True)
@qparam("action", multiple=True)
@qparam("resource_type")
@qparam("resource_id", type=const.QPARAM_TYPE_INT, default=None)
def select_groups(qparams):
    """Search groups in dynamic selections.

    Uses :func:`kadi.lib.resources.api.get_selected_resources`.
    """
    excluded_ids = qparams["exclude"]
    resource_type = qparams["resource_type"]
    resource_id = qparams["resource_id"]

    # If applicable, exclude groups that already have any role in the specified
    # resource.
    if (
        resource_type in const.RESOURCE_TYPES
        and resource_type != "group"
        and resource_id is not None
    ):
        model = get_class_by_name(const.RESOURCE_TYPES[resource_type]["model"])
        resource = model.query.get_active(resource_id)

        if resource is not None and has_permission(
            current_user, "read", resource_type, resource_id
        ):
            group_ids_query = get_group_roles(
                resource_type, object_id=resource_id
            ).with_entities(Group.id)
            excluded_ids += [g.id for g in group_ids_query]

    return get_selected_resources(
        Group,
        page=qparams["page"],
        filter_term=qparams["term"],
        exclude=excluded_ids,
        actions=qparams["action"],
    )
