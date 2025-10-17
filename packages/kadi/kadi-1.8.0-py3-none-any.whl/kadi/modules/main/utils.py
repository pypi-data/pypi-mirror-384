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
from flask_login import current_user

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.favorites.models import Favorite
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.search.models import SavedSearch
from kadi.lib.search.schemas import SavedSearchSchema
from kadi.lib.utils import get_class_by_name
from kadi.lib.web import url_for


def get_favorite_resources(max_items=6, user=None):
    """Get a list of serialized resources favorited by the given user.

    :param max_items: (optional) The maximum number of resource to return.
    :param user: (optional) The user the favorite resources belong to. Defaults to the
        current user.
    :return: The serialized resources as a list of dictionaries, each resource
        additionally containing its type in a human-readable manner as ``pretty_type``.
    """
    user = user if user is not None else current_user

    resource_queries = []

    for resource_type, resource_type_meta in const.RESOURCE_TYPES.items():
        favorite_ids_query = user.favorites.filter(
            Favorite.object == resource_type
        ).with_entities(Favorite.object_id)

        if not favorite_ids_query.count():
            continue

        model = get_class_by_name(resource_type_meta["model"])

        # Only query the ID, modification date and type, as the resulting resources will
        # not be serialized as-is.
        resources_query = (
            get_permitted_objects(user, "read", resource_type)
            .filter(
                model.state == const.MODEL_STATE_ACTIVE,
                model.id.in_(favorite_ids_query),
            )
            .with_entities(
                model.id,
                model.last_modified.label("last_modified"),
                db.literal(resource_type).label("type"),
            )
        )

        resource_queries.append(resources_query)

    if not resource_queries:
        return []

    resources = (
        resource_queries[0]
        .union(*resource_queries[1:])
        .order_by(db.desc("last_modified"))
        .limit(max_items)
    )

    serialized_resources = []

    for resource in resources:
        resource_type_meta = const.RESOURCE_TYPES[resource.type]

        model = get_class_by_name(resource_type_meta["model"])
        schema = get_class_by_name(resource_type_meta["schema"])

        serialized_resources.append(
            {
                **schema(_internal=True).dump(model.query.get(resource.id)),
                "pretty_type": resource_type_meta["title"],
            }
        )

    return serialized_resources


def get_resource_searches(user=None):
    """Get a list of serialized saved resource searches of the given user.

    :param user: (optional) The user the saved searches belong to. Defaults to the
        current user.
    :return: The serialized searches as a list of dictionaries, each search additionally
        containing its corresponding resource type in a human-readable manner as
        ``pretty_type``.
    """
    user = user if user is not None else current_user

    whens = [
        (resource_type, index)
        for index, resource_type in enumerate(const.RESOURCE_TYPES)
    ]
    saved_searches = user.saved_searches.filter(
        SavedSearch.object.in_(const.RESOURCE_TYPES)
    ).order_by(db.case(*whens, value=SavedSearch.object), SavedSearch.name)

    schema = SavedSearchSchema(_internal=True)
    serialized_searches = []

    for saved_search in saved_searches:
        serialized_searches.append(
            {
                **schema.dump(saved_search),
                "pretty_type": const.RESOURCE_TYPES[saved_search.object][
                    "title_plural"
                ],
            }
        )

    return serialized_searches


def _get_resource_data(resource_config, user):
    resource_type = resource_config.get("resource")
    max_items = resource_config.get("max_items", 0)

    if resource_type not in const.RESOURCE_TYPES or not max_items:
        return None

    resource_type_meta = const.RESOURCE_TYPES[resource_type]
    model = get_class_by_name(resource_type_meta["model"])
    schema = get_class_by_name(resource_type_meta["schema"])

    endpoint_args = {}

    explicit_permissions = resource_config.get("explicit_permissions", False)

    if explicit_permissions:
        if resource_type == "group":
            endpoint_args["member_only"] = "true"
        else:
            endpoint_args["explicit_permissions"] = "true"

    if resource_config.get("creator", "any") == "any":
        resources_query = get_permitted_objects(
            user, "read", resource_type, check_defaults=not explicit_permissions
        )
    else:
        resources_query = model.query.filter(model.user_id == user.id)
        endpoint_args["user"] = user.id

    visibility = resource_config.get("visibility", "all")

    if visibility != "all":
        resources_query = resources_query.filter(model.visibility == visibility)
        endpoint_args["visibility"] = visibility

    resources = (
        resources_query.filter(model.state == const.MODEL_STATE_ACTIVE)
        .order_by(model.last_modified.desc())
        .limit(max_items)
        .all()
    )

    if not resources:
        return None

    return {
        "title": str(resource_type_meta["title_plural"]),
        "url": url_for(resource_type_meta["endpoint"], **endpoint_args),
        "items": schema(many=True, _internal=True).dump(resources),
    }


def get_latest_resources(user=None):
    """Get a list of serialized resources according to their modification date.

    Uses the home page layout as configured via the user-specific ``"HOME_LAYOUT"``
    config item to determine how many resources of each type to collect.

    :param user: (optional) The user the layout belongs to. Defaults to the current
        user.
    :return: The serialized resources as a list of dictionaries per resource type, each
        containing the localized resource title (``"title"``), the resource search url
        (``"url"``) and the serialized resources themselves (``"items"``).
    """
    user = user if user is not None else current_user

    home_layout = user.get_config(
        const.USER_CONFIG_HOME_LAYOUT, default=const.USER_CONFIG_HOME_LAYOUT_DEFAULT
    )

    serialized_resources = []

    for resource_config in home_layout:
        resource_data = _get_resource_data(resource_config, user)

        if resource_data is not None:
            serialized_resources.append(resource_data)

    return serialized_resources
