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
from importlib import metadata

from flask_login import current_user
from flask_login import login_required

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.ext.oauth import oauth_server
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import json_response
from kadi.lib.api.core import scopes_required
from kadi.lib.api.utils import create_pagination_data
from kadi.lib.api.utils import status
from kadi.lib.conversion import normalize
from kadi.lib.conversion import strip
from kadi.lib.db import escape_like
from kadi.lib.licenses.core import get_licenses as _get_licenses
from kadi.lib.licenses.schemas import LicenseSchema
from kadi.lib.permissions.utils import get_object_roles
from kadi.lib.tags.core import get_tags as _get_tags
from kadi.lib.tags.schemas import TagSchema
from kadi.lib.utils import get_class_by_name
from kadi.lib.web import paginated
from kadi.lib.web import qparam
from kadi.lib.web import url_for
from kadi.modules.main.schemas import DeletedResourceSchema


@bp.get("")
@login_required
@status(200, "Return the API endpoints.")
def index():
    """Get all base API endpoints."""
    endpoints = {
        "collections": url_for("api.get_collections"),
        "groups": url_for("api.get_groups"),
        "info": url_for("api.get_info"),
        "licenses": url_for("api.get_licenses"),
        "records": url_for("api.get_records"),
        "roles": url_for("api.get_resource_roles"),
        "tags": url_for("api.get_tags"),
        "templates": url_for("api.get_templates"),
        "trash": url_for("api.get_trash"),
        "users": url_for("api.get_users"),
    }
    return json_response(200, endpoints)


@bp.get("/info")
@login_required
@status(200, "Return the information about the Kadi instance.")
def get_info():
    """Get information about the Kadi instance."""
    info = {
        "version": metadata.version("kadi"),
    }
    return json_response(200, info)


@bp.get("/roles")
@login_required
@status(200, "Return the resource roles and permissions.")
def get_resource_roles():
    """Get all possible roles and corresponding permissions/actions of all resources."""
    roles = {}

    for resource_type in const.RESOURCE_TYPES:
        roles[resource_type] = get_object_roles(resource_type)

    return json_response(200, roles)


@bp.get("/tags")
@login_required
@paginated
@qparam(
    "filter", parse=normalize, description="A query to filter the tags by their name."
)
@qparam(
    "type",
    parse=strip,
    default=None,
    choice=["record", "collection"],
    description="A resource type to limit the tags to.",
)
@status(200, "Return a paginated array of tags, sorted by name in ascending order.")
def get_tags(page, per_page, qparams):
    """Get tags of resources the current user can access."""
    paginated_tags = _get_tags(
        filter_term=qparams["filter"], resource_type=qparams["type"]
    ).paginate(page=page, per_page=per_page, error_out=False)

    data = {
        "items": TagSchema(many=True).dump(paginated_tags),
        **create_pagination_data(paginated_tags.total, page, per_page, **qparams),
    }

    return json_response(200, data)


@bp.get("/licenses")
@login_required
@paginated
@qparam(
    "filter",
    parse=normalize,
    description="A query to filter the licenses by their title or name.",
)
@status(
    200, "Return a paginated array of licenses, sorted by title in ascending order."
)
def get_licenses(page, per_page, qparams):
    """Get available licenses."""
    paginated_licenses = _get_licenses(filter_term=qparams["filter"]).paginate(
        page=page, per_page=per_page, error_out=False
    )

    data = {
        "items": LicenseSchema(many=True).dump(paginated_licenses),
        **create_pagination_data(paginated_licenses.total, page, per_page, **qparams),
    }

    return json_response(200, data)


@bp.get("/trash")
@login_required
@scopes_required("misc.manage_trash")
@paginated
@qparam(
    "filter",
    parse=normalize,
    description="A query to filter the deleted resources by their identifier.",
)
@status(
    200,
    "Return a paginated array of deleted resources, sorted by deletion date in"
    " descending order.",
)
def get_trash(page, per_page, qparams):
    """Get deleted resources the current user created.

    Only the `id` and `identifier` of the resources are returned. Additionally, each
    resource contains its resource type (`type`), its deletion date (`deleted_at`) as
    well as endpoints to restore (`_actions.restore`) or purge (`_actions.purge`) the
    resource.
    """
    queries = []

    for resource_type, resource_type_meta in const.RESOURCE_TYPES.items():
        model = get_class_by_name(resource_type_meta["model"])

        resources_query = model.query.filter(
            model.state == const.MODEL_STATE_DELETED,
            model.user_id == current_user.id,
            model.identifier.ilike(f"%{escape_like(qparams['filter'])}%"),
        ).with_entities(
            model.id,
            model.identifier,
            model.last_modified.label("last_modified"),
            db.literal(resource_type).label("type"),
        )
        queries.append(resources_query)

    paginated_resources = (
        queries[0]
        .union(*queries[1:])
        .order_by(db.desc("last_modified"))
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    items = DeletedResourceSchema(many=True).dump(paginated_resources)
    data = {
        "items": items,
        **create_pagination_data(paginated_resources.total, page, per_page),
    }

    return json_response(200, data)


@bp.route("/oauth/userinfo", methods=["GET", "POST"])
def openid_userinfo():
    """Get the user info provided by OpenID connect."""
    return oauth_server.create_endpoint_response("userinfo")
