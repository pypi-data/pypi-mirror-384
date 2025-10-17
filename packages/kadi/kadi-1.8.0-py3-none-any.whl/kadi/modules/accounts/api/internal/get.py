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
from flask import render_template
from flask_login import current_user
from flask_login import login_required

import kadi.lib.constants as const
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import internal
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.api.utils import create_pagination_data
from kadi.lib.conversion import strip
from kadi.lib.favorites.models import Favorite
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.utils import get_user_roles
from kadi.lib.storage.misc import preview_thumbnail
from kadi.lib.utils import get_class_by_name
from kadi.lib.web import paginated
from kadi.lib.web import qparam
from kadi.modules.accounts.models import User
from kadi.modules.accounts.models import UserState
from kadi.modules.accounts.utils import get_filtered_user_ids


@bp.get("/users/<int:id>/image")
@login_required
@internal
def preview_user_image(id):
    """Preview a user's profile image directly in the browser."""
    user = User.query.get_or_404(id)

    if user.is_merged:
        return json_error_response(404)

    if user.image_name:
        return preview_thumbnail(str(user.image_name), "user.jpg")

    return json_error_response(404)


@bp.get("/users/favorites/<resource_type>")
@login_required
@internal
@paginated
def get_favorite_resources(resource_type, page, per_page):
    """Get favorited resources of a specific type of the current user."""
    if resource_type not in const.RESOURCE_TYPES:
        return json_error_response(404)

    model = get_class_by_name(const.RESOURCE_TYPES[resource_type]["model"])
    schema = get_class_by_name(const.RESOURCE_TYPES[resource_type]["schema"])

    paginated_resources = (
        get_permitted_objects(current_user, "read", resource_type)
        .filter(
            model.state == const.MODEL_STATE_ACTIVE,
            model.id.in_(
                current_user.favorites.filter(
                    Favorite.object == resource_type
                ).with_entities(Favorite.object_id)
            ),
        )
        .order_by(model.last_modified.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    data = {
        "items": schema(many=True).dump(paginated_resources),
        **create_pagination_data(
            paginated_resources.total, page, per_page, resource_type=resource_type
        ),
    }

    return json_response(200, data)


@bp.get("/users/select")
@login_required
@internal
@qparam("page", type=const.QPARAM_TYPE_INT, default=1)
@qparam("term", parse=strip)
@qparam("exclude", type=const.QPARAM_TYPE_INT, multiple=True)
@qparam("resource_type")
@qparam("resource_id", type=const.QPARAM_TYPE_INT, default=None)
def select_users(qparams):
    """Search users in dynamic selections.

    Similar to :func:`kadi.lib.resources.api.get_selected_resources`.
    """
    excluded_ids = qparams["exclude"]
    resource_type = qparams["resource_type"]
    resource_id = qparams["resource_id"]

    # If applicable, exclude users that already have any role in the specified resource.
    if resource_type in const.RESOURCE_TYPES and resource_id is not None:
        model = get_class_by_name(const.RESOURCE_TYPES[resource_type]["model"])
        resource = model.query.get_active(resource_id)

        if resource is not None and has_permission(
            current_user, "read", resource_type, resource_id
        ):
            user_ids_query = get_user_roles(
                resource_type, object_id=resource_id
            ).with_entities(User.id)
            excluded_ids += [u.id for u in user_ids_query]

    paginated_users = (
        User.query.filter(
            User.id.in_(get_filtered_user_ids(qparams["term"])),
            User.id.notin_(excluded_ids),
            User.state == UserState.ACTIVE,
        )
        .order_by(User.displayname)
        .paginate(page=qparams["page"], per_page=10, error_out=False)
    )

    data = {
        "results": [],
        "pagination": {"more": paginated_users.has_next},
    }
    for user in paginated_users:
        data["results"].append(
            {
                "id": user.id,
                "text": f"@{user.identity.username}",
                "body": render_template(
                    "accounts/snippets/select_user.html",
                    displayname=user.displayname,
                    username=user.identity.username,
                    type=user.identity.Meta.identity_type["name"],
                ),
            }
        )

    return json_response(200, data)
