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

from kadi.lib.conversion import truncate
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.resources.utils import get_filtered_resources
from kadi.lib.resources.utils import get_linked_resources
from kadi.lib.resources.utils import search_resources
from kadi.lib.tags.models import Tag
from kadi.lib.web import url_for
from kadi.modules.records.links import _calculate_link_graph_meta
from kadi.modules.records.models import Record
from kadi.modules.records.models import RecordLink
from kadi.modules.records.models import RecordState

from .models import Collection
from .models import CollectionState


def search_collections(
    search_query=None,
    page=1,
    per_page=10,
    sort="_score",
    visibility=None,
    explicit_permissions=False,
    user_ids=None,
    tags=None,
    tag_operator="or",
    user=None,
):
    """Search and filter for collections.

    Uses :func:`kadi.lib.resources.utils.get_filtered_resources` and
    :func:`kadi.lib.resources.utils.search_resources`.

    :param search_query: (optional) See
        :func:`kadi.lib.resources.utils.search_resources`.
    :param page: (optional) See :func:`kadi.lib.resources.utils.search_resources`.
    :param per_page: (optional) See :func:`kadi.lib.resources.utils.search_resources`.
    :param sort: (optional) See :func:`kadi.lib.resources.utils.search_resources`.
    :param visibility: (optional) See
        :func:`kadi.lib.resources.utils.get_filtered_resources`.
    :param explicit_permissions: (optional) See
        :func:`kadi.lib.resources.utils.get_filtered_resources`.
    :param user_ids: (optional) See
        :func:`kadi.lib.resources.utils.get_filtered_resources`.
    :param tags: (optional) A list of tag names to filter the collections with.
    :param tag_operator: (optional) The operator to filter the tags with. One of
        ``"or"`` or ``"and"``.
    :param user: (optional) The user to check for any permissions regarding the searched
        collections. Defaults to the current user.
    :return: The search results as returned by
        :func:`kadi.lib.resources.utils.search_resources`.
    """
    user = user if user is not None else current_user

    collections_query = get_filtered_resources(
        Collection,
        visibility=visibility,
        explicit_permissions=explicit_permissions,
        user_ids=user_ids,
        user=user,
    )

    if tags:
        if tag_operator == "and":
            tag_filters = []

            for tag in tags:
                tag_filters.append(Collection.tags.any(Tag.name == tag))

            collections_query = collections_query.filter(*tag_filters)
        else:
            # Always fall back to "or" otherwise.
            collections_query = collections_query.join(Collection.tags).filter(
                Tag.name.in_(tags)
            )

    collection_ids = [c.id for c in collections_query.with_entities(Collection.id)]

    return search_resources(
        Collection,
        search_query=search_query,
        page=page,
        per_page=per_page,
        sort=sort,
        filter_ids=collection_ids,
    )


def get_parent_collections(collection, user=None):
    """Recursively get all parents of a collection that a user can access.

    In this context having access to a collection means having read permission for it.
    Note that as soon as a parent collection is not accessible or inactive, no further
    potential parents are collected.

    :param collection: The collection to get the parents of.
    :param user: (optional) The user to check for access permissions when retrieving the
        collections. Defaults to the current user.
    :return: A list of parent collections starting with the immediate parent of the
        given collection.
    """
    user = user if user is not None else current_user

    collection_ids_query = (
        get_permitted_objects(user, "read", "collection")
        .filter(Collection.state == CollectionState.ACTIVE)
        .with_entities(Collection.id)
    )
    collection_ids = {c.id for c in collection_ids_query}

    parents = []
    current_parent = collection.parent

    while current_parent is not None:
        if current_parent.id not in collection_ids:
            return parents

        parents.append(current_parent)
        current_parent = current_parent.parent

    return parents


def get_child_collections(collection, user=None):
    """Recursively get all children of a collection that a user can access.

    In this context having access to a collection means having read permission for it.
    Note that if a collection is not accessible or inactive, no further potential
    children of this collection are collected.

    :param collection: The collection to get the children of.
    :param user: (optional) The user to check for access permissions when retrieving the
        collections. Defaults to the current user.
    :return: A list of child collections in unspecified order.
    """
    user = user if user is not None else current_user

    collection_ids_query = (
        get_permitted_objects(user, "read", "collection")
        .filter(Collection.state == CollectionState.ACTIVE)
        .with_entities(Collection.id)
    )
    collection_ids = {c.id for c in collection_ids_query}

    children = []
    collections_to_process = [collection]

    while collections_to_process:
        current_collection = collections_to_process.pop()

        for child in current_collection.children:
            if child.id not in collection_ids:
                continue

            children.append(child)
            collections_to_process.append(child)

    return children


def get_child_collection_records(collection, actions=None, user=None):
    """Recursively get all records of a collection hierarchy that a user can access.

    In this context, the collection hierarchy refers to the given collection and all its
    direct or indirect children. Having access to a child collection or record means
    having read permission for it.

    Uses :func:`get_child_collections` to determine the children of the given
    collection.

    :param collection: The collection to get the children and records of.
    :param actions: (optional) A list of further actions to check as part of the access
        permissions of records.
    :param user: (optional) The user to check for access permissions when retrieving the
        collections and records. Defaults to the current user.
    :return: The records as query. Note that duplicate records are already filtered out.
    """
    actions = actions if actions is not None else []
    user = user if user is not None else current_user

    child_collections = get_child_collections(collection, user=user)
    collection_ids = [collection.id] + [c.id for c in child_collections]

    records_query = get_permitted_objects(user, "read", "record").filter(
        Record.state == RecordState.ACTIVE
    )

    for action in set(actions):
        records_query = get_permitted_objects(user, action, "record").intersect(
            records_query
        )

    return (
        records_query.join(Record.collections)
        .filter(Collection.id.in_(collection_ids))
        .distinct()
    )


def _get_collection_graph_data(collection):
    endpoint = "api.get_collection_links_graph"

    return {
        "id": collection.id,
        "identifier": truncate(collection.identifier, 25),
        "identifier_full": collection.identifier,
        "url": url_for(
            "collections.view_collection",
            id=collection.id,
            tab="links",
            visualize="true",
        ),
        "records_endpoint": url_for(endpoint, id=collection.id, links="records"),
        "children_endpoint": url_for(endpoint, id=collection.id, links="children"),
        "records": None,
        "record_links": None,
        "children": None,
    }


def get_collection_links_graph(collection, records=False, children=False, user=None):
    """Get the links of a collection for visualizing them in a graph.

    Used in conjunction with *D3.js* to visualize the collection links in a graph.

    :param collection: The collection to get the links of.
    :param records: (optional) Whether to include the records (and their links) of the
        given collection.
    :param children: (optional) Whether to include the children of the given collection.
    :param user: (optional) The user to check for access permissions regarding the
        linked resources. Defaults to the current user.
    :return: A dictionary containing the metadata of the given collection, optionally
        including its records (``"records"``), record links (``"record_links"``) and its
        children (``"children"``).
    """
    user = user if user is not None else current_user

    data = _get_collection_graph_data(collection)

    if records:
        # Limit the records of the collection to a maximum of 1000.
        records_query = (
            get_linked_resources(Record, collection.records, user=user)
            .order_by(Record.last_modified.desc())
            .limit(1000)
        )

        record_ids = []
        data["records"] = []

        for record in records_query:
            record_ids.append(record.id)
            data["records"].append(
                {
                    "id": f"{collection.id}-{record.id}",
                    "identifier": truncate(record.identifier, 25),
                    "identifier_full": record.identifier,
                    "type": truncate(record.type, 25),
                    "type_full": record.type,
                    "url": url_for(
                        "records.view_record",
                        id=record.id,
                        tab="links",
                        visualize="true",
                    ),
                }
            )

        # Also limit the links between the records of the collection to a maximum of
        # 1000.
        record_links_query = (
            RecordLink.query.filter(
                RecordLink.record_from_id.in_(record_ids),
                RecordLink.record_to_id.in_(record_ids),
            )
            .order_by(RecordLink.last_modified.desc())
            .limit(1000)
        )

        data["record_links"] = []

        for record_link in record_links_query:
            data["record_links"].append(
                {
                    "id": f"{collection.id}-{record_link.id}",
                    "source": f"{collection.id}-{record_link.record_from_id}",
                    "target": f"{collection.id}-{record_link.record_to_id}",
                    "name": truncate(record_link.name, 25),
                    "name_full": record_link.name,
                    # We simply take the outgoing record as base for the URL.
                    "url": url_for(
                        "records.view_record_link",
                        record_id=record_link.record_from_id,
                        link_id=record_link.id,
                    ),
                }
            )

        # Add the link indices and lengths to the data.
        _calculate_link_graph_meta(data["record_links"])

    if children:
        data["children"] = []

        # Limit the children of the collection to a maximum of 100.
        child_collections_query = (
            get_linked_resources(Collection, collection.children, user=user)
            .order_by(Collection.last_modified.desc())
            .limit(100)
        )

        for child in child_collections_query:
            data["children"].append(_get_collection_graph_data(child))

    return data
