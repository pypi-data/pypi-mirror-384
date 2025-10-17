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

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.conversion import normalize
from kadi.lib.conversion import strip
from kadi.lib.db import escape_like
from kadi.lib.exceptions import KadiPermissionError
from kadi.lib.favorites.core import toggle_favorite
from kadi.lib.permissions.core import add_role as _add_role
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.core import remove_role as _remove_role
from kadi.lib.permissions.models import Role
from kadi.lib.permissions.utils import get_group_roles
from kadi.lib.permissions.utils import get_object_roles
from kadi.lib.permissions.utils import get_user_roles
from kadi.lib.resources.schemas import GroupResourceRoleSchema
from kadi.lib.resources.schemas import UserResourceRoleSchema
from kadi.lib.utils import compact_json
from kadi.lib.web import download_bytes
from kadi.lib.web import qparam
from kadi.lib.web import url_for
from kadi.modules.accounts.models import User
from kadi.modules.accounts.utils import get_filtered_user_ids
from kadi.modules.groups.models import Group

from .utils import add_link as _add_link
from .utils import remove_link as _remove_link


def add_link(relationship, resource, user=None):
    """Convenience function to link two resources together.

    For ease of use in API endpoints. Uses :func:`kadi.lib.resources.utils.add_link`.

    Note that this function may issue a database commit.

    :param relationship: See :func:`kadi.lib.resources.utils.add_link`.
    :param resource: See :func:`kadi.lib.resources.utils.add_link`.
    :param user: (optional) See :func:`kadi.lib.resources.utils.add_link`.
    :return: A JSON response depending on the success of the operation.
    """
    user = user if user is not None else current_user

    try:
        if _add_link(relationship, resource, user=user):
            db.session.commit()
            return json_response(201)

        return json_error_response(409, description="Link already exists.")

    except KadiPermissionError as e:
        return json_error_response(403, description=str(e))


def remove_link(relationship, resource, user=None):
    """Convenience function to remove the link between two resources.

    For ease of use in API endpoints. Uses :func:`kadi.lib.resources.utils.remove_link`.

    Note that this function may issue a database commit.

    :param relationship: See :func:`kadi.lib.resources.utils.remove_link`.
    :param resource: See :func:`kadi.lib.resources.utils.remove_link`.
    :param user: (optional) See :func:`kadi.lib.resources.utils.remove_link`.
    :return: A JSON response depending on the success of the operation.
    """
    user = user if user is not None else current_user

    try:
        if _remove_link(relationship, resource, user=user):
            db.session.commit()
            return json_response(204)

        return json_error_response(404, description="Link does not exist.")

    except KadiPermissionError as e:
        return json_error_response(403, description=str(e))


def add_role(subject, resource, role_name, user=None):
    """Convenience function to add an existing role to a user or group.

    For ease of use in API endpoints. Uses :func:`kadi.lib.permissions.core.add_role`.

    Note that this function may issue a database commit.

    :param subject: See :func:`kadi.lib.permissions.core.add_role`.
    :param resource: The resource the role refers to. An instance of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param role_name: See :func:`kadi.lib.permissions.core.add_role`.
    :param user: (optional) The user performing the operation. Defaults to the current
        user.
    :return: A JSON response depending on the success of the operation.
    """
    user = user if user is not None else current_user

    if isinstance(subject, Group) and not has_permission(
        user, "read", "group", subject.id
    ):
        return json_error_response(
            403, description="No permission to add role to group."
        )

    try:
        if _add_role(subject, resource.__tablename__, resource.id, role_name):
            db.session.commit()
            return json_response(201)

        return json_error_response(
            409, description="A role for that resource already exists."
        )

    except ValueError as e:
        return json_error_response(400, description=str(e))


def remove_role(subject, resource):
    """Convenience function to remove an existing role of a user or group.

    For ease of use in API endpoints. Uses
    :func:`kadi.lib.permissions.core.remove_role`.

    Note that this function may issue a database commit.

    :param subject: See :func:`kadi.lib.permissions.core.remove_role`.
    :param resource: The resource the role refers to. An instance of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :return: A JSON response depending on the success of the operation.
    """
    if isinstance(subject, User) and subject == resource.creator:
        return json_error_response(409, description="Cannot remove the creator's role.")

    try:
        if _remove_role(subject, resource.__tablename__, resource.id):
            db.session.commit()
            return json_response(204)

        return json_error_response(404, description="Role does not exist.")

    except ValueError as e:
        return json_error_response(400, description=str(e))


def change_role(subject, resource, role_name):
    """Convenience function to change an existing role of a user or group.

    For ease of use in API endpoints. If the given subject is the creator of the given
    resource, the role will not be changed. Uses
    :func:`kadi.lib.permissions.core.remove_role` and
    :func:`kadi.lib.permissions.core.add_role`.

    Note that this function may issue a database commit or rollback.

    :param subject: The :class:`.User` or :class:`.Group`.
    :param resource: The resource the role refers to. An instance of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param role_name: The name of the role to change.
    :return: A JSON response depending on the success of the operation.
    """
    if isinstance(subject, User) and subject == resource.creator:
        return json_error_response(409, description="Cannot change the creator's role.")

    try:
        if _remove_role(subject, resource.__tablename__, resource.id):
            if _add_role(subject, resource.__tablename__, resource.id, role_name):
                db.session.commit()
                return json_response(204)

            return json_error_response(
                409, description="A role for that resource already exists."
            )

        return json_error_response(404, description="Role does not exist.")

    except ValueError as e:
        return json_error_response(400, description=str(e))


def toggle_favorite_resource(resource, user=None):
    """Toggle the favorite state of a resource.

    Uses :func:`toggle_favorite` with the type and ID of the given resource.

    Note that this function issues a database commit.

    :param resource: The resource whose favorite state should be toggled. An instance of
        :class:`.Record`, :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param user: (optional) The user the favorite resource belongs to. Defaults to the
        current user.
    :return: A JSON response indicating the success of the operation.
    """
    user = user if user is not None else current_user

    toggle_favorite(resource.__tablename__, resource.id, user=user)

    db.session.commit()
    return json_response(204)


def get_selected_resources(
    model, page=1, filter_term="", exclude=None, actions=None, filters=None, user=None
):
    """Convenience function to search resources for use in dynamic selections.

    For ease of use in API endpoints. Used in conjunction with *Select2* to search
    resources via dynamic select fields. Only the resources the given user has read
    permission for are returned.

    :param model: The resource model to search, one of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param page: (optional) The current page.
    :param filter_term: (optional) A (case insensitive) term to filter the resources by
        their title, identifier or ID, if the filter can be converted to a valid digit.
    :param exclude: (optional) A list of resource IDs to exclude in the results.
        Defaults to an empty list.
    :param actions: (optional) A list of further actions to check as part of the access
        permissions.
    :param filters: (optional) A list of additional filter expressions to apply to the
        respective resource query.
    :param user: (optional) The user performing the search. Defaults to the current
        user.
    :return: A JSON response containing the results in the following form:

        .. code-block:: json

            {
                "results": [
                    {
                        "id": 1,
                        "text": "@identifier",
                        "endpoint": "<resource API endpoint",
                        "body": "<HTML body>"
                    }
                ],
                "pagination": {
                    "more": true
                }
            }
    """
    exclude = exclude if exclude is not None else []
    actions = actions if actions is not None else []
    filters = filters if filters is not None else []
    user = user if user is not None else current_user

    object_name = model.__tablename__
    filter_term = escape_like(filter_term)

    term_filters = [
        model.title.ilike(f"%{filter_term}%"),
        model.identifier.ilike(f"%{filter_term}%"),
    ]

    if filter_term.isdigit():
        term_filters.append(model.id == int(filter_term))

    resources_query = get_permitted_objects(user, "read", object_name).filter(
        model.state == const.MODEL_STATE_ACTIVE,
        model.id.notin_(exclude),
        db.or_(*term_filters),
    )

    if filters:
        resources_query = resources_query.filter(*filters)

    for action in set(actions):
        resources_query = get_permitted_objects(user, action, object_name).intersect(
            resources_query
        )

    paginated_resources = resources_query.order_by(model.title).paginate(
        page=page, per_page=10, error_out=False
    )

    data = {
        "results": [],
        "pagination": {"more": paginated_resources.has_next},
    }
    for resource in paginated_resources:
        data["results"].append(
            {
                "id": resource.id,
                "text": f"@{resource.identifier}",
                "endpoint": url_for(f"api.get_{object_name}", id=resource.id),
                "body": render_template(
                    "snippets/resources/select.html", resource=resource
                ),
            }
        )

    return json_response(200, data)


def get_resource_user_roles(
    resource, page=1, per_page=10, filter_term="", exclude=None
):
    """Get the paginated user roles of a resource.

    :param resource: The resource to get the user roles of. An instance of
        :class:`.Record`, :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param page: (optional) The current page.
    :param per_page: (optional) Items per page.
    :param filter_term: (optional) A (case insensitive) term to filter the users by
        their username or display name.
    :param exclude: (optional) A list of user IDs to exclude in the results.
    :return: A tuple containing a list of deserialized user roles and the total amount
        of user roles.
    """
    exclude = exclude if exclude is not None else []
    object_name = resource.__class__.__tablename__

    whens = []

    for index, role in enumerate(get_object_roles(object_name)):
        whens.append((role["name"], index))

    paginated_user_roles = (
        get_user_roles(object_name, object_id=resource.id)
        .filter(
            User.id.in_(get_filtered_user_ids(filter_term)),
            User.id.notin_(exclude),
        )
        .order_by(
            (User.id == resource.user_id).desc(),
            db.case(*whens, value=Role.name).desc(),
            User.id,
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    items = UserResourceRoleSchema(obj=resource).dump_from_iterable(
        paginated_user_roles
    )

    return items, paginated_user_roles.total


def get_resource_group_roles(resource, page=1, per_page=10, filter_term="", user=None):
    """Get the paginated group roles of a resource.

    This includes the special case of the given user not having read access to a group
    (any more) but wanting to update permissions of the group, if the permissions of the
    user allow them to. Since such groups should still be listed, they are included
    using a limited subset of group attributes.

    :param resource: The resource to get the group roles of. An instance of
        :class:`.Record`, :class:`.Collection` or :class:`.Template`.
    :param page: (optional) The current page.
    :param per_page: (optional) Items per page.
    :param filter_term: (optional) A query to filter the groups by their title or
        identifier.
    :param user: (optional) The user to check for any permissions regarding the
        resulting groups. Defaults to the current user.
    :return: A tuple containing a list of deserialized group roles and the total amount
        of user roles.
    """
    user = user if user is not None else current_user

    object_name = resource.__class__.__tablename__
    filter_term = escape_like(filter_term)

    group_ids_query = get_permitted_objects(user, "read", "group").with_entities(
        Group.id
    )

    # Already filtered for active groups.
    group_roles_query = get_group_roles(object_name, object_id=resource.id).filter(
        db.or_(
            Group.title.ilike(f"%{filter_term}%"),
            Group.identifier.ilike(f"%{filter_term}%"),
        )
    )

    # Check whether we have the special case of including all group roles.
    include_all_groups = False

    if has_permission(user, "permissions", object_name, resource.id):
        include_all_groups = True
    else:
        group_roles_query = group_roles_query.filter(Group.id.in_(group_ids_query))

    whens = []

    for index, role in enumerate(get_object_roles(object_name)):
        whens.append((role["name"], index))

    paginated_group_roles = group_roles_query.order_by(
        db.case(*whens, value=Role.name).desc(), Group.id
    ).paginate(page=page, per_page=per_page, error_out=False)

    items = GroupResourceRoleSchema(obj=resource).dump_from_iterable(
        paginated_group_roles
    )

    if include_all_groups:
        group_ids = {g.id for g in group_ids_query}

        for item in items:
            group = item["group"]

            if group["id"] not in group_ids:
                # Replace the group metadata with a limited subset of group attributes.
                item["group"] = {
                    "id": group["id"],
                    "title": group["title"],
                    "identifier": group["identifier"],
                    "visibility": group["visibility"],
                }

    return items, paginated_group_roles.total


def get_internal_resource_export(
    resource,
    export_type,
    export_func,
    export_filter=None,
    preview=False,
    download=False,
):
    """Get the exported data of a resource for direct preview or download.

    Only used internally, as the preview functionality of exported data is only useful
    in a browser context.

    :param resource: The resource to export. An instance of :class:`.Record` or
        :class:`.Collection`.
    :param export_type: A valid export type for the resource as defined in
        :const:`kadi.lib.constants.EXPORT_TYPES`.
    :param export_func: The export function corresponding to the resource to export.
    :param export_filter: (optional) A dictionary specifying various export filters,
        which is passed to the given export function.
    :param preview: (optional) Whether the exported data should be sent directly to the
        browser for preview instead of returning a URL. Only relevant for certain export
        types.
    :param download: (optional) Whether the exported data should be downloaded as an
        attachment instead of just previewed.
    :return: The exported data as a corresponding response object, depending on the
        given arguments.
    """
    export_filter = export_filter if export_filter is not None else {}
    object_name = resource.__class__.__tablename__

    export_types = const.EXPORT_TYPES[object_name]

    if export_type not in export_types:
        return json_error_response(404)

    file_ext = export_types[export_type]["ext"]
    filename = f"{resource.identifier}.{file_ext}"

    if export_type in {const.EXPORT_TYPE_JSON, const.EXPORT_TYPE_RDF}:
        return download_bytes(
            export_func(resource, export_type, export_filter=export_filter),
            filename=filename,
            as_attachment=download,
        )

    # For these preview types, the preview flag is used to distinguish between returning
    # a URL, for preview within an HTML element, and returning the data for direct
    # preview in the browser.
    if export_type in {const.EXPORT_TYPE_PDF, const.EXPORT_TYPE_QR}:
        if preview or download:
            return download_bytes(
                export_func(resource, export_type, export_filter=export_filter),
                filename=filename,
                as_attachment=download,
            )

        return json_response(
            200,
            url_for(
                f"api.get_{object_name}_export_internal",
                id=resource.id,
                export_type=export_type,
                preview="true",
                filter=compact_json(export_filter),
            ),
        )

    if export_type == const.EXPORT_TYPE_RO_CRATE:
        # Check whether only the JSON-LD file should be generated for preview or the
        # complete crate.
        if not download:
            export_filter["metadata_only"] = True

            return download_bytes(
                export_func(resource, export_type, export_filter=export_filter),
                filename=f"{resource.identifier}.jsonld",
            )

        export_data = export_func(resource, export_type, export_filter=export_filter)

        return download_bytes(
            export_data,
            filename=filename,
            mimetype=const.MIMETYPE_ZIP,
            content_length=len(export_data),
        )

    return json_response(404)


def filter_qparam(resource_type):
    """Decorator to add a common filter query parameter to a resource API endpoint.

    :param resource_type: The resource type as plural. Only used to generate a suitable
        parameter description.
    """
    return qparam(
        "filter",
        parse=normalize,
        description=f"A query to filter the {resource_type} by their title or"
        " identifier.",
    )


def sort_qparam(resource_type):
    """Decorator to add a common sort query parameter to a resource API endpoint.

    :param resource_type: The resource type as plural. Only used to generate a suitable
        parameter description.
    """
    return qparam(
        "sort",
        parse=strip,
        default="-last_modified",
        choice=[
            "last_modified",
            "-last_modified",
            "created_at",
            "-created_at",
            "title",
            "-title",
            "identifier",
            "-identifier",
        ],
        description=f"The order of the returned {resource_type}.",
    )
