# Copyright 2024 Karlsruhe Institute of Technology
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

from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.api.utils import is_internal_api_request
from kadi.lib.oauth.utils import get_oauth2_client
from kadi.lib.oauth.utils import get_oauth2_client_token
from kadi.lib.oauth.utils import get_oauth2_providers
from kadi.lib.utils import find_dict_in_list
from kadi.lib.web import url_for


def get_federated_instances(include_credentials=False, user=None):
    """Get a list of federated Kadi instances.

    Makes use of the ``FEDERATED_INSTANCES`` specified in the application's
    configuration.

    :param include_credentials: (optional) Whether to include the client ID
        (``"client_id"``) and secret (``"client_secret"``) in the returned instances.
    :param user: (optional) The user who should be checked for whether they are
        connected with the OAuth2 provider of each corresponding instance, in which case
        the ``"is_connected"`` key will be included in the returned instances.
    :return: A list of instance dictionaries in the following form:

        .. code-block:: python3

            [
                {
                    "name": "example",
                    "title": "Kadi4Mat Example",
                    "url": "https://kadi4mat.example.edu",
                    "client_id": "<client_id>",
                    "client_secret": "<client_secret>",
                    "is_connected": True,
                },
            ]
    """
    instances = []
    oauth2_providers = None

    if user is not None:
        oauth2_providers = get_oauth2_providers(user=user)

    for name, config in current_app.config["FEDERATED_INSTANCES"].items():
        instance_invalid = False

        for item in ["url", "client_id", "client_secret"]:
            if item not in config:
                instance_invalid = True
                current_app.logger.error(
                    "Missing URL, client ID and/or client secret in configuration of"
                    f" federated instance '{name}'."
                )

        if instance_invalid:
            continue

        instance = {
            "name": name,
            "title": config.get("title", name),
            "url": config["url"],
        }

        if include_credentials:
            instance["client_id"] = config["client_id"]
            instance["client_secret"] = config["client_secret"]

        if oauth2_providers is not None:
            oauth2_provider = find_dict_in_list(oauth2_providers, "name", name)
            instance["is_connected"] = oauth2_provider["is_connected"]

        instances.append(instance)

    return instances


def get_federated_instance(name, include_credentials=False, user=None):
    """Get a specific federated Kadi instance.

    :param name: The unique name of the instance.
    :param include_credentials: (optional) See :func:`get_federated_instances`.
    :param user: (optional) See :func:`get_federated_instances`.
    :return: The instance in a format as described in :func:`get_federated_instances` or
        ``None`` if no instance with the given name could be found.
    """
    instances = get_federated_instances(
        include_credentials=include_credentials, user=user
    )
    return find_dict_in_list(instances, "name", name)


def federated_request(name, endpoint, params=None, user=None):
    """Perform a HTTP GET request in a federated Kadi instance.

    :param name: The unique name of the instance.
    :param endpoint: The endpoint to request as path.
    :param params: (optional) A dictionary of additional query parameters to include in
        the request.
    :param user: (optional) The user who is performing the request. Defaults to the
        current user.
    :return: A JSON response depending on the success of the operation.
    """
    params = params if params is not None else {}
    user = user if user is not None else current_user

    instance = get_federated_instance(name, user=user)

    if not instance:
        return json_error_response(
            400, description=f"No federated instance '{name}' found."
        )

    response_kwargs = {
        "description": f"Federated instance '{name}' requires a service that is not yet"
        " connected to your account."
    }

    # Only include this information in internal requests for now.
    if is_internal_api_request():
        response_kwargs["_links"] = {
            "connect": url_for("settings.oauth2_provider_login", provider=name)
        }

    error_response = json_error_response(400, **response_kwargs)

    if not instance["is_connected"]:
        return error_response

    oauth2_client_token = get_oauth2_client_token(name, user=user, refresh=True)

    if oauth2_client_token is None:
        return error_response

    token = oauth2_client_token.to_authlib_token()
    client = get_oauth2_client(name)

    if endpoint.startswith("/"):
        endpoint = endpoint[1:]

    try:
        response = client.get(endpoint, token=token, params=params, timeout=10)
    except Exception as e:
        current_app.logger.exception(e)
        return json_error_response(
            502, description=f"Request to instance '{name}' failed."
        )

    return json_response(response.status_code, response.json())
