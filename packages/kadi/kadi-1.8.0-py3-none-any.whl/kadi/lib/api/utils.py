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
import math
import re
from collections import OrderedDict
from functools import wraps

from flask import has_request_context
from flask import request

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import get_class_by_tablename
from kadi.lib.utils import rgetattr
from kadi.lib.web import get_apispec_meta
from kadi.lib.web import url_for


def is_api_request():
    """Check if the current request is an API request.

    A request is an API request if the path of the current request path starts with
    ``"/api"``.

    :return: ``True`` if the request is an API request, ``False`` otherwise.
    """
    return (
        has_request_context()
        and re.search(r"^\/api($|\/.*)$", request.path) is not None
    )


def is_internal_api_request():
    """Check if the current API request is an "internal" one.

    An API request is marked as internal if it includes a query parameter ``_internal``
    with any value (e.g. ``"https://...?_internal=true"``). This can be useful for e.g.
    returning additional data that is only relevant for internal use. Note that it does
    not matter whether the request uses the session or an access token.

    :return: ``True`` if the request is internal, ``False`` otherwise.
    """
    return is_api_request() and request.args.get("_internal") is not None


def get_api_version(default=const.API_VERSION_DEFAULT):
    """Get the API version from the current request.

    :param default: (optional) The API version to return if the current request is an
        API request but does not contain a valid version.
    :return: The current API version or the given ``default`` value as fallback. If the
        current request is not an API request at all, ``None`` will be returned.
    """
    if is_api_request():
        parts = request.path[1:].split("/")

        if len(parts) >= 2:
            api_version = parts[1]

            if api_version in const.API_VERSIONS:
                return api_version

        return default

    return None


def get_access_token_scopes():
    """Get all available access token scopes.

    The available scopes are combined from all resource actions and all additional
    scopes defined in :const:`kadi.lib.constants.ACCESS_TOKEN_SCOPES`.

    :return: A dictionary mapping a scope's object to a list of corresponding actions.
    """
    scopes = {}

    for tablename in db.metadata.tables:
        model = get_class_by_tablename(tablename)
        permissions_meta = rgetattr(model, "Meta.permissions")

        if permissions_meta is not None:
            actions = []

            for action in permissions_meta.get("actions", {}):
                if action not in actions:
                    actions.append(action)

            scopes[tablename] = actions

    order = {
        name: i for i, name in enumerate(["record", "collection", "template", "group"])
    }
    scopes = (
        dict(sorted(scopes.items(), key=lambda item: order.get(item[0], len(order))))
        | const.ACCESS_TOKEN_SCOPES
    )

    return scopes


def create_pagination_data(total, page, per_page, endpoint=None, **kwargs):
    r"""Create pagination information for use in a JSON response.

    Since the pagination data will include links to the current, next and previous
    "pages", the necessary information to build said links needs to be given as well,
    i.e. the endpoint and its corresponding URL parameters.

    :param total: The total amount of items.
    :param page: The current page.
    :param per_page: Items per page.
    :param endpoint: The endpoint used to build links to the current, next and previous
        page. Defaults to the endpoint of the current request.
    :param \**kwargs: Additional keyword arguments to build the links with.
    :return: The pagination information as dictionary in the following form:

        .. code-block:: python3

            {
                "_pagination": {
                    "page": 2,
                    "per_page": 10,
                    "total_pages": 3,
                    "total_items": 25,
                    "_links": {
                        "prev": "https://...?page=1&...",
                        "self": "https://...?page=2&...",
                        "next": "https://...?page=3&...",
                    }
                }
            }

        The list of items is initially empty and can be filled afterwards with whatever
        data should be returned. Note that the links to the previous and next pages are
        only present if the respective page actually exists.
    """
    endpoint = endpoint if endpoint is not None else request.endpoint

    has_next = total > page * per_page
    has_prev = page > 1
    total_pages = math.ceil(total / per_page) or 1

    url_args = {"endpoint": endpoint, "per_page": per_page, **kwargs}

    data = {
        "_pagination": {
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_items": total,
            "_links": {"self": url_for(page=page, **url_args)},
        },
    }

    if has_next:
        data["_pagination"]["_links"]["next"] = url_for(page=page + 1, **url_args)
    if has_prev:
        data["_pagination"]["_links"]["prev"] = url_for(page=page - 1, **url_args)

    return data


def status(status_code, description):
    """Decorator to add response status information to an API endpoint.

    This information is currently only used when generating the API specification.

    :param status_code: The status code of the response.
    :param description: The description corresponding to the status code, describing
        when it occurs or whether there is a response body. Supports basic Markdown
        syntax.
    """

    def decorator(func):
        apispec_meta = get_apispec_meta(func)

        status_meta = apispec_meta.get(const.APISPEC_STATUS_KEY, OrderedDict())
        status_meta[status_code] = description
        status_meta.move_to_end(status_code, last=False)

        if const.APISPEC_STATUS_KEY not in apispec_meta:
            apispec_meta[const.APISPEC_STATUS_KEY] = status_meta

        return func

    return decorator


def reqschema(schema, description="", bind=True):
    """Decorator to add request body information to an API endpoint using a schema.

    This information is mainly used when generating the API specification.

    :param schema: The schema class or instance to use as base for the request body
        information.
    :param description: (optional) Additional description of the request body. Supports
        basic Markdown syntax.
    :param bind: (optional) Flag indicating whether the schema should also be injected
        into the decorated function as keyword argument ``schema``.
    """
    if isinstance(schema, type):
        schema = schema()

    def decorator(func):
        apispec_meta = get_apispec_meta(func)
        apispec_meta[const.APISPEC_REQ_SCHEMA_KEY] = {
            "schema": schema,
            "description": description,
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            if bind:
                kwargs["schema"] = schema

            return func(*args, **kwargs)

        return wrapper

    return decorator


def reqheaders(headers):
    """Decorator to add custom request header information to an API endpoint.

    This information is currently only used when generating the API specification.

    :param headers: The custom request header information as a dictionary in the
        following form:

        .. code-block:: python3

            {
                "<header>": {
                    "type": "integer",
                    "required": True,
                    # Supports basic Markdown syntax.
                    "description": "",
                }
            }
    """

    def decorator(func):
        apispec_meta = get_apispec_meta(func)
        apispec_meta[const.APISPEC_REQ_HEADERS_KEY] = headers

        return func

    return decorator
