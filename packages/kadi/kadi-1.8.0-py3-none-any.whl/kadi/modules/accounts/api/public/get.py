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
from flask_login import current_user
from flask_login import login_required

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.api.core import scopes_required
from kadi.lib.api.utils import create_pagination_data
from kadi.lib.api.utils import status
from kadi.lib.conversion import strip
from kadi.lib.db import escape_like
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.resources.api import filter_qparam
from kadi.lib.resources.api import sort_qparam
from kadi.lib.resources.utils import get_order_column
from kadi.lib.utils import get_class_by_name
from kadi.lib.web import paginated
from kadi.lib.web import qparam
from kadi.modules.accounts.models import User
from kadi.modules.accounts.models import UserState
from kadi.modules.accounts.schemas import IdentitySchema
from kadi.modules.accounts.schemas import UserSchema
from kadi.modules.accounts.utils import get_filtered_user_ids
from kadi.modules.groups.models import Group
from kadi.modules.groups.models import GroupState
from kadi.modules.groups.schemas import GroupSchema
from kadi.modules.groups.utils import get_user_groups as _get_user_groups


@bp.get("/users")
@login_required
@scopes_required("user.read")
@paginated
@qparam(
    "filter",
    parse=strip,
    description="A query to filter the users by their display name or username.",
)
@qparam(
    "inactive",
    type=const.QPARAM_TYPE_BOOL,
    default=False,
    description="Flag indicating whether inactive users should be returned as well.",
)
@status(
    200,
    "Return a paginated array of users, sorted by creation date in descending order.",
)
def get_users(page, per_page, qparams):
    """Get registered users."""
    states = [UserState.ACTIVE]

    if qparams["inactive"]:
        states.append(UserState.INACTIVE)

    paginated_users = (
        User.query.filter(
            User.id.in_(get_filtered_user_ids(qparams["filter"])),
            User.state.in_(states),
        )
        .order_by(User.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    data = {
        "items": UserSchema(many=True).dump(paginated_users),
        **create_pagination_data(paginated_users.total, page, per_page, **qparams),
    }

    return json_response(200, data)


@bp.get("/users/me")
@login_required
@scopes_required("user.read")
@status(200, "Return the current user.")
def get_current_user():
    """Get the currently authenticated user."""
    return json_response(200, UserSchema().dump(current_user))


@bp.get("/users/<int:id>")
@login_required
@scopes_required("user.read")
@status(200, "Return the user.")
def get_user(id):
    """Get the user specified by the given ID."""
    user = User.query.get_or_404(id)

    if user.is_merged:
        return json_error_response(404)

    return json_response(200, UserSchema().dump(user))


@bp.get("/users/<identity_type>/<username>")
@login_required
@scopes_required("user.read")
@status(200, "Return the user.")
def get_user_by_identity(identity_type, username):
    """Get the user specified by the given identity type and username."""
    provider_config = current_app.config["AUTH_PROVIDERS"].get(identity_type)

    if provider_config is None:
        return json_error_response(404)

    identity_class = provider_config["identity_class"]
    identity = identity_class.query.filter_by(username=username).first_or_404()

    # No need to check whether the user was merged, as all identities are migrated to
    # the new user.
    return json_response(200, UserSchema().dump(identity.user))


@bp.get("/users/<int:id>/identities")
@login_required
@scopes_required("user.read")
@status(
    200, "Return an array of identities, sorted by creation date in ascending order."
)
def get_user_identities(id):
    """Get all identities of the user specified by the given ID."""
    user = User.query.get_or_404(id)

    if user.is_merged:
        return json_error_response(404)

    identities = user.identities.order_by("created_at")
    return json_response(200, IdentitySchema(many=True).dump(identities))


def _get_user_resources(resource_type, user_id, page, per_page, qparams):
    user = User.query.get_or_404(user_id)

    if user.is_merged:
        return json_error_response(404)

    model = get_class_by_name(const.RESOURCE_TYPES[resource_type]["model"])
    schema = get_class_by_name(const.RESOURCE_TYPES[resource_type]["schema"])

    filter_term = escape_like(qparams["filter"])
    order_column = get_order_column(model, qparams["sort"])

    resource_creator = user
    resource_viewer = current_user

    if shared := qparams["shared"]:
        resource_creator = current_user
        resource_viewer = user

    paginated_resources = (
        get_permitted_objects(
            resource_viewer, "read", resource_type, check_defaults=not shared
        )
        .filter(
            model.state == const.MODEL_STATE_ACTIVE,
            model.user_id == resource_creator.id,
            db.or_(
                model.title.ilike(f"%{filter_term}%"),
                model.identifier.ilike(f"%{filter_term}%"),
            ),
        )
        .order_by(order_column)
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    data = {
        "items": schema(many=True).dump(paginated_resources),
        **create_pagination_data(
            paginated_resources.total, page, per_page, id=user.id, **qparams
        ),
    }

    return json_response(200, data)


@bp.get("/users/<int:id>/records")
@login_required
@scopes_required("user.read", "record.read")
@paginated
@filter_qparam("records")
@sort_qparam("records")
@qparam(
    "shared",
    type=const.QPARAM_TYPE_BOOL,
    default=False,
    description="Flag indicating whether records the user created should be returned or"
    " records created by the current user that were explicitly shared with the user.",
)
@status(200, "Return a paginated array of records.")
def get_user_records(id, page, per_page, qparams):
    """Get created or shared records of the user specified by the given ID."""
    return _get_user_resources("record", id, page, per_page, qparams)


@bp.get("/users/<int:id>/collections")
@login_required
@scopes_required("user.read", "collection.read")
@paginated
@filter_qparam("collections")
@sort_qparam("collections")
@qparam(
    "shared",
    type=const.QPARAM_TYPE_BOOL,
    default=False,
    description="Flag indicating whether collections the user created should be"
    " returned or collections created by the current user that were explicitly shared"
    " with the user.",
)
@status(200, "Return a paginated array of collections.")
def get_user_collections(id, page, per_page, qparams):
    """Get created or shared collections of the user specified by the given ID."""
    return _get_user_resources("collection", id, page, per_page, qparams)


@bp.get("/users/<int:id>/templates")
@login_required
@scopes_required("user.read", "template.read")
@paginated
@filter_qparam("templates")
@sort_qparam("templates")
@qparam(
    "shared",
    type=const.QPARAM_TYPE_BOOL,
    default=False,
    description="Flag indicating whether templates the user created should be returned"
    " or templates created by the current user that were explicitly shared with the"
    " user.",
)
@status(200, "Return a paginated array of templates.")
def get_user_templates(id, page, per_page, qparams):
    """Get created or shared templates of the user specified by the given ID."""
    return _get_user_resources("template", id, page, per_page, qparams)


@bp.get("/users/<int:id>/groups")
@login_required
@scopes_required("user.read", "group.read")
@paginated
@filter_qparam("groups")
@sort_qparam("groups")
@qparam(
    "common",
    type=const.QPARAM_TYPE_BOOL,
    default=False,
    description="Flag indicating whether groups the user created should be returned or"
    " groups that the current user and the specified user have in common regarding"
    " group membership.",
)
@status(200, "Return a paginated array of groups.")
def get_user_groups(id, page, per_page, qparams):
    """Get created or common groups of the user specified by the given ID."""
    user = User.query.get_or_404(id)

    if user.is_merged:
        return json_error_response(404)

    if qparams["common"]:
        # No need to check the permissions separately in this case because of the
        # intersection.
        groups_query = _get_user_groups(user).intersect(_get_user_groups(current_user))
    else:
        groups_query = get_permitted_objects(current_user, "read", "group").filter(
            Group.state == GroupState.ACTIVE, Group.user_id == user.id
        )

    filter_term = escape_like(qparams["filter"])
    paginated_groups = (
        groups_query.filter(
            db.or_(
                Group.title.ilike(f"%{filter_term}%"),
                Group.identifier.ilike(f"%{filter_term}%"),
            )
        )
        .order_by(Group.last_modified.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    data = {
        "items": GroupSchema(many=True).dump(paginated_groups),
        **create_pagination_data(
            paginated_groups.total, page, per_page, id=user.id, **qparams
        ),
    }

    return json_response(200, data)
