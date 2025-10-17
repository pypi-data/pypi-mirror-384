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
from datetime import timedelta

from elasticsearch.dsl import Q as Query
from elasticsearch.exceptions import ConnectionError as ESConnectionError
from flask import current_app
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

import kadi.lib.constants as const
from kadi.lib.db import NestedTransaction
from kadi.lib.exceptions import KadiPermissionError
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.permissions.core import has_permission
from kadi.lib.utils import is_quoted
from kadi.lib.utils import utcnow
from kadi.modules.collections.core import purge_collection
from kadi.modules.collections.models import Collection
from kadi.modules.groups.core import purge_group
from kadi.modules.groups.models import Group
from kadi.modules.records.core import purge_record
from kadi.modules.records.models import Record
from kadi.modules.templates.core import purge_template
from kadi.modules.templates.models import Template


def get_filtered_resources(
    model, visibility=None, explicit_permissions=False, user_ids=None, user=None
):
    """Convenience function to get filtered resources of a specific model.

    :param model: The model to filter. One of :class:`.Record`, :class:`.Collection`,
        :class:`.Template` or :class:`.Group`.
    :param visibility: (optional) A visibility value to filter the resources with.
    :param explicit_permissions: (optional) Flag indicating whether only resources with
        explicit access permissions for the given user should be included, independent
        of the given visibility value.
    :param user_ids: (optional) A list of user IDs to filter the creators of the
        resources with.
    :param user: (optional) The user to check for any permissions regarding the filtered
        resources. Defaults to the current user.
    :return: The filtered resources as query.
    """
    user = user if user is not None else current_user

    resources_query = get_permitted_objects(
        user, "read", model.__tablename__, check_defaults=not explicit_permissions
    ).filter(model.state == const.MODEL_STATE_ACTIVE)

    if visibility in {
        const.RESOURCE_VISIBILITY_PRIVATE,
        const.RESOURCE_VISIBILITY_PUBLIC,
    }:
        resources_query = resources_query.filter(model.visibility == visibility)

    if user_ids:
        resources_query = resources_query.filter(model.user_id.in_(user_ids))

    return resources_query


def search_resources(
    model,
    search_query=None,
    page=1,
    per_page=10,
    sort="_score",
    filter_ids=None,
    extra_es_query=None,
):
    """Convenience function to query the search index of a specific model.

    Uses :meth:`.SearchableMixin.search` for the given model.

    :param model: The model to search. One of :class:`.Record`, :class:`.Collection`,
        :class:`.Template` or :class:`.Group`.
    :param search_query: (optional) The search query string.
    :param page: (optional) The current page.
    :param per_page: (optional) The amount of search results per page.
    :param sort: (optional) The name of a field to sort on. One of ``"_score"``,
        ``"last_modified"``, ``"-last_modified"``, ``"created_at"``, ``"-created_at"``,
        ``"title"``, ``"-title"``, ``"identifier"`` or ``"-identifier"``. Falls back to
        ``"-last_modified"`` if no search query is given.
    :param filter_ids: (optional) A list of resource IDs to restrict the search results
        to.
    :param extra_es_query: (optional) An additional Elasticsearch DSL query object to
        combine with the given search query, if applicable.
    :return: A tuple containing a list of the search results and the total amount of
        hits.
    """
    es_query = None

    if search_query:
        if is_quoted(search_query):
            # For quoted queries, run a multi match phrase query on all regularly
            # indexed text fields. The quotes in the query are already ignored by
            # Elasticsearch in this case.
            es_query = Query(
                "multi_match",
                query=search_query,
                type="phrase",
                fields=["identifier.text^3", "title.text^3", "plain_description"],
            )
        else:
            if len(search_query) < 3:
                # For very short queries (i.e. smaller than the indexed trigrams),
                # perform a multi match phrase prefix query on the regularly indexed
                # identifier and title field and combine it with a match phrase query on
                # the description field.
                prefix_query = Query(
                    "multi_match",
                    query=search_query,
                    type="phrase_prefix",
                    fields=["identifier.text", "title.text"],
                )
                phrase_query = Query("match_phrase", plain_description=search_query)

                es_query = Query("bool", should=[prefix_query, phrase_query])
            else:
                # In all other cases, perform a regular multi match query on all
                # regularly indexed fields and combine it with a similar query using all
                # fields as well as fuzzy matching, but weighted less heavily.
                match_query = Query(
                    "multi_match",
                    query=search_query,
                    fields=["identifier.text^3", "title.text^3", "plain_description"],
                    boost=5,
                )
                fuzzy_query = Query(
                    "multi_match",
                    query=search_query,
                    fields=[
                        "identifier.text^3",
                        "title.text^3",
                        "plain_description",
                        "identifier^0.5",
                        "title^0.5",
                    ],
                    fuzziness="AUTO:2,6",
                )

                es_query = Query("bool", should=[match_query, fuzzy_query])

    # Combine the basic Elasticsearch DSL query object with the given one using an AND
    # operation, if applicable.
    if extra_es_query is not None:
        if search_query:
            es_query = Query("bool", must=[es_query, extra_es_query])
        else:
            es_query = extra_es_query

    if sort not in {
        "_score",
        "last_modified",
        "-last_modified",
        "created_at",
        "-created_at",
        "title",
        "-title",
        "identifier",
        "-identifier",
    }:
        sort = "_score"

    if sort == "_score":
        # Sort by score first and by last_modified second. This also works for the case
        # of no search query being used at all.
        sort = ["_score", "-last_modified"]

    elif sort in {"title", "-title", "identifier", "-identifier"}:
        # We need to use the keyword field to sort by text property.
        sort += ".keyword"

    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    try:
        return model.search(
            query=es_query,
            sort=sort,
            filter_ids=filter_ids,
            start=start_index,
            end=end_index,
        )
    except ESConnectionError:
        if not current_app.config["ELASTICSEARCH_ENABLE_FALLBACK"]:
            return [], 0

        # Use a regular query as fallback that just applies the filtered resource IDs.
        paginated_resources = (
            model.query.filter(model.id.in_(filter_ids))
            .order_by(model.last_modified.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return paginated_resources.items, paginated_resources.total


def get_order_column(model, sort):
    """Convenience function to retrieve a column of a resource's model for ordering.

    :param model: The model to retrieve the column of. One of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param sort: A string representing the order column and direction. One of
        "``last_modified``", "``-last_modified``", "``created_at``", "``-created_at``",
        "``title``", "``-title``", "``identifier``" or "``-identifier``".
    :return: The order column.
    """
    if sort == "last_modified":
        return model.last_modified
    if sort == "-last_modified":
        return model.last_modified.desc()
    if sort == "created_at":
        return model.created_at
    if sort == "-created_at":
        return model.created_at.desc()
    if sort == "title":
        return model.title
    if sort == "-title":
        return model.title.desc()
    if sort == "identifier":
        return model.identifier
    if sort == "-identifier":
        return model.identifier.desc()

    return model.last_modified.desc()


def add_link(relationship, resource, user=None):
    """Convenience function to link two resources together.

    Note that only the link-permission of the given resource is checked.

    :param relationship: The many-relationship to append the resource to.
    :param resource: The resource to link. An instance of :class:`.Record` or
        :class:`.Collection`.
    :param user: (optional) The user performing the link operation. Defaults to the
        current user.
    :return: ``True`` if the link was established successfully, ``False`` if the link
        already exists.
    :raises KadiPermissionError: If the user performing the operation does not have the
        necessary permissions.
    """
    user = user if user is not None else current_user

    if not has_permission(user, "link", resource.__tablename__, resource.id):
        raise KadiPermissionError("No permission to link resources.")

    if resource not in relationship:
        with NestedTransaction(exc=IntegrityError) as t:
            relationship.append(resource)

        return t.success

    return False


def remove_link(relationship, resource, user=None):
    """Convenience function to remove the link between two resources.

    Note that only the link-permission of the given resource is checked.

    :param relationship: The many-relationship to remove the resource from.
    :param resource: The resource to remove. An instance of :class:`.Record` or
        :class:`.Collection`.
    :param user: (optional) The user performing the link operation. Defaults to the
        current user.
    :return: ``True`` if the link was removed successfully, ``False`` if the link does
        not exist.
    :raises KadiPermissionError: If the user performing the operation does not have the
        necessary permissions.
    """
    user = user if user is not None else current_user

    if not has_permission(user, "link", resource.__tablename__, resource.id):
        raise KadiPermissionError("No permission to unlink resources.")

    if resource in relationship:
        with NestedTransaction(exc=StaleDataError) as t:
            relationship.remove(resource)

        return t.success

    return False


def get_linked_resources(model, relationship, actions=None, user=None):
    """Convenience function to get all linked resources that a user can access.

    In this context having access to a resource means having read permission for that
    resource.

    :param model: The model class corresopnding to the linked resources. One of
        :class:`.Record` or :class:`.Collection`.
    :param relationship: The many-relationship that represents the linked resources to
        get.
    :param actions: (optional) A list of further actions to check as part of the access
        permissions.
    :param user: (optional) The user who will be checked for access permissions.
        Defaults to the current user.
    :return: The resulting query of the linked resources.
    """
    actions = actions if actions is not None else []
    user = user if user is not None else current_user

    object_ids_query = (
        get_permitted_objects(user, "read", model.__tablename__)
        .filter(model.state == const.MODEL_STATE_ACTIVE)
        .with_entities(model.id)
    )

    for action in set(actions):
        object_ids_query = (
            get_permitted_objects(user, action, model.__tablename__)
            .with_entities(model.id)
            .intersect(object_ids_query)
        )

    return relationship.filter(model.id.in_(object_ids_query))


def _clean_resources(model, purge_func, inside_task):
    expiration_date = utcnow() - timedelta(seconds=const.DELETED_RESOURCES_MAX_AGE)
    resources = model.query.filter(
        model.state == const.MODEL_STATE_DELETED, model.last_modified < expiration_date
    )

    if inside_task and resources.count() > 0:
        current_app.logger.info(
            f"Cleaning {resources.count()} deleted {model.__tablename__}(s)."
        )

    for resource in resources:
        purge_func(resource)


def clean_resources(inside_task=False):
    """Clean all expired, deleted resources.

    Note that this function may issue one or more database commits.

    :param inside_task: (optional) A flag indicating whether the function is executed in
        a task. In that case, additional information will be logged.
    """
    _clean_resources(Record, purge_record, inside_task)
    _clean_resources(Collection, purge_collection, inside_task)
    _clean_resources(Template, purge_template, inside_task)
    _clean_resources(Group, purge_group, inside_task)


def _purge_resources(model, purge_func, user, timestamp, inside_task):
    resources = model.query.filter(
        model.user_id == user.id, model.state == const.MODEL_STATE_DELETED
    )

    if timestamp is not None:
        resources = resources.filter(model.last_modified < timestamp)

    if inside_task and resources.count() > 0:
        current_app.logger.info(
            f"Purging {resources.count()} deleted {model.__tablename__}(s)."
        )

    for resource in resources:
        purge_func(resource)


def purge_resources(user=None, timestamp=None, inside_task=False):
    """Purge all deleted resources created by a given user.

    Note that this function may issue one or more database commits.

    :param user: (optional) The user the resources to purge were created by. Defaults to
        the current user.
    :param timestamp: (optional) A timestamp as datetime object to limit the resources
        to be purged to the ones older than this timestamp regarding their last
        modification date.
    :param inside_task: (optional) A flag indicating whether the function is executed in
        a task. In that case, additional information will be logged.
    """
    user = user if user is not None else current_user

    args = [user, timestamp, inside_task]

    _purge_resources(Record, purge_record, *args)
    _purge_resources(Collection, purge_collection, *args)
    _purge_resources(Template, purge_template, *args)
    _purge_resources(Group, purge_group, *args)
