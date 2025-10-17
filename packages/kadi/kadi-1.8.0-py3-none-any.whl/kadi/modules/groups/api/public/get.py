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
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import filter_qparam
from kadi.lib.resources.api import get_resource_user_roles
from kadi.lib.resources.api import sort_qparam
from kadi.lib.resources.utils import get_order_column
from kadi.lib.revisions.schemas import ObjectRevisionSchema
from kadi.lib.utils import get_class_by_name
from kadi.lib.web import paginated
from kadi.lib.web import qparam
from kadi.lib.web import url_for
from kadi.modules.groups.models import Group
from kadi.modules.groups.models import GroupState
from kadi.modules.groups.schemas import GroupSchema
from kadi.modules.groups.utils import search_groups


@bp.get("/groups")
@login_required
@scopes_required("group.read")
@paginated(page_max=100)
@qparam(
    "query",
    parse=strip,
    description="A query to search the groups with. Supports exact matches when"
    " surrounded by double quotes.",
)
@qparam(
    "sort",
    parse=strip,
    default="_score",
    choice=[
        "_score",
        "last_modified",
        "-last_modified",
        "created_at",
        "-created_at",
        "title",
        "-title",
        "identifier",
        "-identifier",
    ],
    description="The order of the search results. Falls back to `-last_modified` if no"
    " search query is given.",
)
@qparam(
    "visibility",
    parse=strip,
    choice=[const.RESOURCE_VISIBILITY_PRIVATE, const.RESOURCE_VISIBILITY_PUBLIC],
    description="A visibility value to filter the groups with.",
)
@qparam(
    "member_only",
    type=const.QPARAM_TYPE_BOOL,
    default=False,
    description="Flag indicating whether only groups with membership should be"
    " included, independent of their visibility.",
)
@qparam(
    "user",
    type=const.QPARAM_TYPE_INT,
    multiple=True,
    description="User IDs to filter the groups with in relation to their creator. All"
    " given users are filtered using an *OR* operation.",
)
@status(200, "Return a paginated array of groups.")
def get_groups(page, per_page, qparams):
    """Search and filter for groups."""
    groups, total_groups = search_groups(
        search_query=qparams["query"],
        page=page,
        per_page=per_page,
        sort=qparams["sort"],
        visibility=qparams["visibility"],
        user_ids=qparams["user"],
        member_only=qparams["member_only"],
    )

    data = {
        "items": GroupSchema(many=True).dump(groups),
        "_actions": {"new_group": url_for("api.new_group")},
        **create_pagination_data(total_groups, page, per_page, **qparams),
    }

    return json_response(200, data)


@bp.get("/groups/<int:id>")
@permission_required("read", "group", "id")
@scopes_required("group.read")
@status(200, "Return the group.")
def get_group(id):
    """Get the group specified by the given ID."""
    group = Group.query.get_active_or_404(id)
    return json_response(200, GroupSchema().dump(group))


@bp.get("/groups/identifier/<identifier:identifier>")
@login_required
@scopes_required("group.read")
@status(200, "Return the group.")
def get_group_by_identifier(identifier):
    """Get the group specified by the given identifier."""
    group = Group.query.filter_by(
        identifier=identifier, state=GroupState.ACTIVE
    ).first_or_404()

    if not has_permission(current_user, "read", "group", group.id):
        return json_error_response(403)

    return json_response(200, GroupSchema().dump(group))


@bp.get("/groups/<int:id>/members")
@permission_required("read", "group", "id")
@scopes_required("group.read", "user.read")
@paginated
@qparam(
    "filter",
    parse=strip,
    description="A query to filter the members by their username or display name.",
)
@qparam(
    "exclude",
    type=const.QPARAM_TYPE_INT,
    multiple=True,
    description="User IDs to exclude.",
)
@status(
    200,
    "Return a paginated array of members, sorted by role name and then by user ID in"
    " ascending order. The creator will always be listed first.",
)
def get_group_members(id, page, per_page, qparams):
    """Get members of the group specified by the given ID."""
    group = Group.query.get_active_or_404(id)

    items, total = get_resource_user_roles(
        group,
        page=page,
        per_page=per_page,
        filter_term=qparams["filter"],
        exclude=qparams["exclude"],
    )
    data = {
        "items": items,
        **create_pagination_data(total, page, per_page, id=group.id),
    }

    return json_response(200, data)


def _get_group_resources(resource_type, group_id, page, per_page, qparams):
    group = Group.query.get_active_or_404(group_id)

    model = get_class_by_name(const.RESOURCE_TYPES[resource_type]["model"])
    schema = get_class_by_name(const.RESOURCE_TYPES[resource_type]["schema"])

    filter_term = escape_like(qparams["filter"])
    order_column = get_order_column(model, qparams["sort"])

    paginated_resources = (
        get_permitted_objects(current_user, "read", resource_type)
        .intersect(
            get_permitted_objects(group, "read", resource_type, check_defaults=False)
        )
        .filter(
            model.state == const.MODEL_STATE_ACTIVE,
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
            paginated_resources.total, page, per_page, id=group.id, **qparams
        ),
    }

    return json_response(200, data)


@bp.get("/groups/<int:id>/records")
@permission_required("read", "group", "id")
@scopes_required("group.read", "record.read")
@paginated
@filter_qparam("records")
@sort_qparam("records")
@status(200, "Return a paginated array of records.")
def get_group_records(id, page, per_page, qparams):
    """Get records shared with the group with the given ID.

    Shared means that the group needs to have explicit read permission for a record.
    """
    return _get_group_resources("record", id, page, per_page, qparams)


@bp.get("/groups/<int:id>/collections")
@permission_required("read", "group", "id")
@scopes_required("group.read", "collection.read")
@paginated
@filter_qparam("collections")
@sort_qparam("collections")
@status(200, "Return a paginated array of collections.")
def get_group_collections(id, page, per_page, qparams):
    """Get collections shared with the group with the given ID.

    Shared means that the group needs to have explicit read permission for a collection.
    """
    return _get_group_resources("collection", id, page, per_page, qparams)


@bp.get("/groups/<int:id>/templates")
@permission_required("read", "group", "id")
@scopes_required("group.read", "template.read")
@paginated
@filter_qparam("templates")
@sort_qparam("templates")
@status(200, "Return a paginated array of templates.")
def get_group_templates(id, page, per_page, qparams):
    """Get templates shared with the group with the given ID.

    Shared means that the group needs to have explicit read permission for a template.
    """
    return _get_group_resources("template", id, page, per_page, qparams)


@bp.get("/groups/<int:id>/revisions")
@permission_required("read", "group", "id")
@scopes_required("group.read")
@paginated
@status(
    200,
    "Return a paginated array of revisions, sorted by revision timestamp in descending"
    " order.",
)
def get_group_revisions(id, page, per_page):
    """Get revisions of the group specified by the given ID."""
    group = Group.query.get_active_or_404(id)
    paginated_revisions = group.ordered_revisions.paginate(
        page=page, per_page=per_page, error_out=False
    )

    schema = ObjectRevisionSchema(
        GroupSchema,
        many=True,
        api_endpoint="api.get_group_revision",
        view_endpoint="groups.view_revision",
        endpoint_args={"group_id": group.id},
    )
    data = {
        "items": schema.dump(paginated_revisions),
        **create_pagination_data(
            paginated_revisions.total, page, per_page, id=group.id
        ),
    }

    return json_response(200, data)


@bp.get("/groups/<int:group_id>/revisions/<int:revision_id>")
@permission_required("read", "group", "group_id")
@scopes_required("group.read")
@qparam(
    "revision",
    type=const.QPARAM_TYPE_INT,
    default=None,
    description="The ID of a revision to compare with instead of the previous one.",
)
@status(200, "Return the revision.")
def get_group_revision(group_id, revision_id, qparams):
    """Get a group revision.

    Will return the revision specified by the given revision ID of the group specified
    by the given group ID.
    """
    group = Group.query.get_active_or_404(group_id)
    revision = group.revisions.filter(
        Group.revision_class.id == revision_id
    ).first_or_404()

    compared_revision = None

    if compared_revision_id := qparams["revision"]:
        compared_revision = group.revisions.filter(
            Group.revision_class.id == compared_revision_id
        ).first()

    schema = ObjectRevisionSchema(
        GroupSchema,
        compared_revision=compared_revision,
        api_endpoint="api.get_group_revision",
        view_endpoint="groups.view_revision",
        endpoint_args={"group_id": group.id},
    )

    return json_response(200, schema.dump(revision))
