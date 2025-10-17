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
from functools import wraps

from flask import abort
from flask import current_app
from flask import has_request_context
from flask import request
from werkzeug.http import HTTP_STATUS_CODES

import kadi.lib.constants as const
from kadi.lib.cache import memoize_request
from kadi.lib.oauth.models import OAuth2ServerToken
from kadi.lib.utils import compact_json
from kadi.lib.web import get_apispec_meta
from kadi.lib.web import get_error_description

from .models import PersonalToken


def json_response(status_code, body=None):
    """Return a JSON response to a client.

    :param status_code: The HTTP status code of the response.
    :param body: (optional) The response body, which must be JSON serializable. Defaults
        to an empty dictionary.
    :return: The JSON response.
    """
    body = body if body is not None else {}

    return current_app.response_class(
        response=compact_json(body), status=status_code, mimetype=const.MIMETYPE_JSON
    )


def json_error_response(status_code, message=None, description=None, **kwargs):
    r"""Return a JSON error response to a client.

    Uses :func:`json_response` with the given headers and a body in the following form,
    assuming no additional error information was provided:

    .. code-block:: json

        {
            "code": 404,
            "message": "<message>",
            "description": "<description>"
        }

    :param status_code: See :func:`json_response`.
    :param message: (optional) The error message. Defaults to a message corresponding to
        the given status code.
    :param description: (optional) The error description. Defaults to the result of
        :func:`kadi.lib.web.get_error_description` using the given status code.
    :param \**kwargs: Additional error information that will be included in the response
        body. All values need to be JSON serializable.
    :return: The JSON response.
    """
    message = (
        message
        if message is not None
        else HTTP_STATUS_CODES.get(status_code, "Unknown Error")
    )
    description = (
        description if description is not None else get_error_description(status_code)
    )

    return json_response(
        status_code,
        {
            "code": status_code,
            "message": message,
            "description": description,
            **kwargs,
        },
    )


@memoize_request
def get_access_token():
    """Get an access token from the current request.

    Currently, this will either be a personal token or an OAuth2 server token. The token
    value has to be included as a *Bearer* token within an *Authorization* header.

    Supports memoization via :func:`kadi.lib.cache.memoize_request`.

    :return: An access token object or ``None`` if no valid token can be found or no
        request context currently exists.
    """
    if (
        has_request_context()
        and request.authorization is not None
        and request.authorization.type == "bearer"
    ):
        token = request.authorization.token

        if token.startswith(const.ACCESS_TOKEN_PREFIX_PAT):
            return PersonalToken.get_by_token(token)

        if token.startswith(const.ACCESS_TOKEN_PREFIX_OAUTH):
            return OAuth2ServerToken.get_by_access_token(token)

        # Fall back to personal tokens, since these used to not include a prefix.
        return PersonalToken.get_by_token(token)

    return None


def check_access_token_scopes(*scopes):
    r"""Check if the current access token contains certain scope values.

    The current access token will be retrieved using :func:`.utils.get_access_token`.

    :param \*scopes: One or multiple scope values to check in the form of
        ``"<object>.<action>"``.
    :return: ``True`` if the access token either contains all given scope values or if
        the current request contains no valid access token at all, ``False`` otherwise.
    """
    access_token = get_access_token()

    if access_token is None:
        return True

    current_scopes = access_token.scope.split()
    valid_scopes = [scope in current_scopes for scope in scopes]

    return all(valid_scopes)


def scopes_required(*scopes):
    r"""Decorator to add required access token scope values to an API endpoint.

    Uses :func:`check_access_token_scopes`, so the scopes are only checked if the
    current request actually contains a valid access token. Therefore, this decorator
    usually only makes sense for public API endpoints that can be accessed by using an
    access token.

    **Example:**

    .. code-block:: python3

        @blueprint.route("/records")
        @login_required
        @scopes_required("record.read")
        def get_records():
            pass

    The information about the scope values is also used when generating the API
    specification.

    :param \*scopes: See :func:`check_access_token_scopes`.
    """

    def decorator(func):
        apispec_meta = get_apispec_meta(func)
        apispec_meta[const.APISPEC_SCOPES_KEY] = scopes

        @wraps(func)
        def wrapper(*args, **kwargs):
            if not check_access_token_scopes(*scopes):
                abort(
                    json_error_response(
                        401,
                        description="Access token has insufficient scope.",
                        scopes=scopes,
                    )
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def internal(func):
    """Decorator to mark an API endpoint as internal.

    Internal endpoints can only be accessed via the session, not via access tokens. This
    is not to be confused with :func:`kadi.lib.api.utils.is_internal_api_request`.

    The information about an endpoint being internal is also used when generating the
    API specification.
    """
    apispec_meta = get_apispec_meta(func)
    apispec_meta[const.APISPEC_INTERNAL_KEY] = True

    @wraps(func)
    def wrapper(*args, **kwargs):
        access_token = get_access_token()

        if access_token is not None:
            abort(404)

        return func(*args, **kwargs)

    return wrapper


def experimental(func):
    """Decorator to mark an API endpoint as experimental.

    Experimental endpoints can only be called if the ``EXPERIMENTAL_FEATURES`` flag in
    the application's configuration is set.

    The information about an endpoint being experimental is also used when generating
    the API specification.
    """
    apispec_meta = get_apispec_meta(func)
    apispec_meta[const.APISPEC_EXPERIMENTAL_KEY] = True

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_app.config["EXPERIMENTAL_FEATURES"]:
            abort(404)

        return func(*args, **kwargs)

    return wrapper
