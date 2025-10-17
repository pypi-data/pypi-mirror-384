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
from time import time

from authlib.common.urls import add_params_to_qs
from flask import current_app
from flask_login import current_user

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.ext.oauth import oauth_registry
from kadi.ext.oauth import oidc_registry
from kadi.lib.exceptions import KadiDecryptionKeyError
from kadi.lib.plugins.core import run_hook
from kadi.lib.security import random_bytes
from kadi.lib.utils import find_dict_in_list
from kadi.lib.utils import flatten_list

from .core import update_oauth2_client_token
from .models import OAuth2ClientToken
from .models import OAuth2ServerAuthCode


def get_oauth2_client(name):
    """Get an OAuth2 client by its name.

    :param name: The name of the OAuth2 client.
    :return: The OAuth2 client.
    :raises AttributeError: If the specified OAuth2 client has not been registered.
    """
    if name not in oauth_registry._clients:
        raise AttributeError(f"OAuth2 client '{name}' is not registered.")

    return oauth_registry._clients[name]


def get_oidc_client(name):
    """Get an OIDC client by its name.

    :param name: The name of the OIDC client.
    :return: The OIDC client.
    :raises AttributeError: If the specified OIDC client has not been registered.
    """
    if name not in oidc_registry._clients:
        raise AttributeError(f"OIDC client '{name}' is not registered.")

    return oidc_registry._clients[name]


def get_oauth2_client_token(name, user=None, refresh=False):
    """Get an OAuth2 client token of a user by its name.

    Note that if either the access token or refresh token cannot be decrypted or if
    ``refresh`` is ``True`` while the access token is expired and cannot be refreshed,
    the client token will be deleted automatically.

    Note that this function may issue a database commit.

    :param name: The name of the client token.
    :param user: (optional) The user the client token belongs to. Defaults to the
        current user.
    :param refresh: (optional) Flag indicating whether the underlying access token
        should be refreshed if it is expired. This requires that the OAuth2 provider
        used to create the token is registered with the application and that a valid
        refresh token is stored as well.
    :return: The OAuth2 client token or ``None`` if no client token could be retrieved
        or refreshed.
    """
    user = user if user is not None else current_user

    oauth2_client_token_query = user.oauth2_client_tokens.filter(
        OAuth2ClientToken.name == name
    )

    try:
        oauth2_client_token = oauth2_client_token_query.first()
    except KadiDecryptionKeyError:
        current_app.logger.error(
            f"Error decrypting OAuth2 client token value(s) for '{name}' of {user!r}."
        )

        oauth2_client_token_query.delete()
        db.session.commit()

        return None

    if oauth2_client_token is not None and oauth2_client_token.is_expired and refresh:
        if oauth2_client_token.refresh_token is None:
            oauth2_client_token_query.delete()
            db.session.commit()

            return None

        try:
            client = get_oauth2_client(name)

            # Since there is no documented way to manually update the access token by
            # using the Flask integration of Authlib, we use the underlying OAuth2
            # session directly.
            token_data = client._get_oauth_client().refresh_token(
                client.access_token_url,
                refresh_token=oauth2_client_token.refresh_token,
                timeout=5,
            )
        except Exception as e:
            current_app.logger.exception(e)

            oauth2_client_token_query.delete()
            db.session.commit()

            return None

        token_args = {
            "access_token": token_data["access_token"],
            "expires_at": token_data.get("expires_at"),
            "expires_in": token_data.get("expires_in"),
        }

        # Only replace the previous refresh token if no new one was issued.
        if "refresh_token" in token_data:
            token_args["refresh_token"] = token_data["refresh_token"]

        update_oauth2_client_token(oauth2_client_token, **token_args)
        db.session.commit()

    return oauth2_client_token


def has_oauth2_providers():
    """Check if at least one OAuth2 provider is registered.

    Uses the :func:`kadi.plugins.spec.kadi_get_oauth2_providers` plugin hook to check
    for potential OAuth2 providers.

    :return: ``True`` if at least one OAuth2 provider is registered, ``False``
        otherwise.
    """
    try:
        providers = flatten_list(run_hook("kadi_get_oauth2_providers"))
    except Exception as e:
        current_app.logger.exception(e)
        return False

    return bool(providers)


def get_oauth2_providers(user=None):
    """Get a list of registered OAuth2 providers.

    Uses the :func:`kadi.plugins.spec.kadi_get_oauth2_providers` plugin hook to collect
    potential OAuth2 providers.

    :param user: (optional) The user who should be checked for whether they are
        connected with an OAuth2 provider, in which case ``"is_connected"`` will be set
        to ``True`` for the respective provider. Defaults to the current user.
    :return: A list of provider dictionaries in the following form, sorted by title:

        .. code-block:: python3

            [
                {
                    "name": "example",
                    "title": "Example provider",
                    "website": "https://example.com",
                    "description": "An example OAuth2 provider.",
                    "is_connected": True,
                },
            ]
    """
    user = user if user is not None else current_user

    try:
        providers = flatten_list(run_hook("kadi_get_oauth2_providers"))
    except Exception as e:
        current_app.logger.exception(e)
        return []

    oauth2_providers = []
    provider_names = set()

    for provider in providers:
        if not isinstance(provider, dict):
            current_app.logger.error("Invalid OAuth2 provider format.")
            continue

        provider_name = provider.get("name")

        if provider_name is None or provider_name not in oauth_registry._registry:
            current_app.logger.error(
                f"OAuth2 provider '{provider_name}' is configured or registered"
                " incorrectly."
            )
            continue

        if provider_name in provider_names:
            current_app.logger.warn(
                f"An OAuth2 provider '{provider_name}' is already registered."
            )
            continue

        provider_names.add(provider_name)

        oauth2_client_token = get_oauth2_client_token(provider_name, user=user)
        oauth2_providers.append(
            {
                "name": provider_name,
                "title": provider.get("title", provider_name),
                "website": provider.get("website", ""),
                "description": provider.get("description", ""),
                "is_connected": oauth2_client_token is not None,
            }
        )

    return sorted(oauth2_providers, key=lambda provider: provider["title"])


def get_oauth2_provider(provider, user=None):
    """Get a specific, registered OAuth2 provider.

    Note that this function may issue one or more database commits.

    :param provider: The unique name of the OAuth2 provider.
    :param user: (optional) See :func:`get_oauth2_providers`.
    :return: The publication provider in a format as described in
        :func:`get_oauth2_providers` or ``None`` if no provider with the given name
        could be found.
    """
    user = user if user is not None else current_user

    providers = get_oauth2_providers(user=user)
    return find_dict_in_list(providers, "name", provider)


def new_oauth2_access_token(*args, include_prefix=True, **kwargs):
    """Create a new random access token value for use in OAuth2 server tokens.

    :param include_prefix: (optional) Whether to include a prefix before the actual
        access token value to distinguish it with other types of access tokens.
    :return: The generated access token value.
    """
    token = random_bytes()

    if include_prefix:
        return f"{const.ACCESS_TOKEN_PREFIX_OAUTH}{token}"

    return token


def new_oauth2_refresh_token(*args, **kwargs):
    """Create a new random refresh token value for use in OAuth2 server tokens.

    :return: The generated refresh token value.
    """
    return random_bytes(num_bytes=32)


def clean_auth_codes(inside_task=False):
    """Clean all expired OAuth2 authorization codes.

    Note that this function issues a database commit.

    :param inside_task: (optional) A flag indicating whether the function is executed in
        a task. In that case, additional information will be logged.
    """
    oauth2_auth_codes = OAuth2ServerAuthCode.query.filter(
        OAuth2ServerAuthCode.auth_time + const.OAUTH_AUTH_CODE_EXPIRES_IN < int(time())
    )

    if inside_task and oauth2_auth_codes.count() > 0:
        current_app.logger.info(
            f"Cleaning {oauth2_auth_codes.count()} expired authorization code(s)."
        )

    for oauth2_auth_code in oauth2_auth_codes:
        db.session.delete(oauth2_auth_code)

    db.session.commit()


def get_refresh_token_handler(client_id, client_secret):
    """Get a handler function for using the OAuth2 refresh token grant via Authlib.

    This handler is necessary since Authlib does not automatically include the client ID
    and secret when requesting new access tokens via the refresh token grant, even
    though this is usually required for clients that were issued a secret.

    :param client_id: The OAuth2 client ID.
    :param client_secret: The OAuth2 client secret.
    :return: A handler function to be defined as a compliance fix hook when registering
        new OAuth2 clients via Authlib.
    """

    def _compliance_fix(session):
        def _refresh_token_request(url, headers, body):
            body = add_params_to_qs(
                body, {"client_id": client_id, "client_secret": client_secret}
            )
            return url, headers, body

        session.register_compliance_hook(
            "refresh_token_request", _refresh_token_request
        )

    return _compliance_fix
