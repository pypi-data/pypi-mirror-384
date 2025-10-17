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
from flask import current_app
from flask_babel import gettext as _
from flask_login import current_user
from markupsafe import Markup

from kadi.ext.db import db
from kadi.lib.oauth.utils import get_oauth2_client
from kadi.lib.oauth.utils import get_oauth2_client_token
from kadi.lib.oauth.utils import get_oauth2_providers
from kadi.lib.plugins.core import run_hook
from kadi.lib.utils import find_dict_in_list
from kadi.lib.utils import flatten_list


def get_publication_providers(resource, user=None):
    """Get a list of registered publication providers.

    Uses the :func:`kadi.plugins.spec.kadi_get_publication_providers` plugin hook to
    collect potential publication providers combined with the information from
    :func:`kadi.lib.oauth.utils.get_oauth2_providers`.

    Note that this function may issue one or more database commits.

    :param resource: The resource to eventually publish, an instance of :class:`.Record`
        or :class:`.Collection`.
    :param user: (optional) The user who should be checked for whether they are
        connected with the OAuth2 provider the publication provider uses, in which case
        ``"is_connected"`` will be set to ``True`` for the respective provider. Defaults
        to the current user.
    :return: A list of provider dictionaries in the following form, sorted by name:

        .. code-block:: python3

            [
                {
                    "name": "example",
                    "description": "An example publication provider.",
                    "title": "Example provider",
                    "website": "https://example.com",
                    "is_connected": True,
                },
            ]
    """
    user = user if user is not None else current_user

    try:
        providers = flatten_list(
            run_hook("kadi_get_publication_providers", resource=resource)
        )
    except Exception as e:
        current_app.logger.exception(e)
        return []

    oauth2_providers = get_oauth2_providers(user=user)

    publication_providers = []
    provider_names = set()

    for provider in providers:
        if not isinstance(provider, dict):
            current_app.logger.error("Invalid publication provider format.")
            continue

        provider_name = provider.get("name")
        # More efficient here to use this over "get_oauth2_provider".
        oauth2_provider = find_dict_in_list(oauth2_providers, "name", provider_name)

        if provider_name is None or oauth2_provider is None:
            current_app.logger.error(f"Invalid publication provider '{provider_name}'.")
            continue

        if provider_name in provider_names:
            current_app.logger.warn(
                f"A publication provider '{provider_name}' is already registered."
            )
            continue

        provider_names.add(provider_name)
        publication_providers.append(
            {
                "name": provider_name,
                "description": Markup(provider.get("description", "")),
                "title": oauth2_provider["title"],
                "website": oauth2_provider["website"],
                "is_connected": oauth2_provider["is_connected"],
            }
        )

    return sorted(publication_providers, key=lambda provider: provider["name"])


def get_publication_provider(provider, resource, user=None):
    """Get a specific, registered publication provider.

    Note that this function may issue one or more database commits.

    :param provider: The unique name of the publication provider.
    :param resource: The resource to eventually publish, an instance of :class:`.Record`
        or :class:`.Collection`.
    :param user: (optional) See :func:`get_publication_providers`.
    :return: The publication provider in a format as described in
        :func:`get_publication_providers` or ``None`` if no provider with the given name
        could be found.
    """
    user = user if user is not None else current_user

    providers = get_publication_providers(resource, user=user)
    return find_dict_in_list(providers, "name", provider)


def publish_resource(provider, resource, form_data=None, user=None, task=None):
    """Publish a resource using a given provider.

    Uses the :func:`kadi.plugins.spec.kadi_publish_resource` plugin hook.

    Note that this function issues one or more database commits.

    :param provider: The unique name of the publication provider.
    :param resource: The resource to publish, an instance of :class:`.Record` or
        :class:`.Collection`.
    :param form_data: (optional) Form data as dictionary to customize the publication
        process.
    :param user: (optional) The user who started the publication process. Defaults to
        the current user.
    :param task: (optional) A :class:`.Task` object that that may be provided if this
        function is executed in a background task.
    :return: A tuple consisting of a flag indicating whether the operation succeeded and
        a (HTML) template further describing the result in a user-readable manner,
        depending on the provider.
    """
    form_data = form_data if form_data is not None else {}
    user = user if user is not None else current_user

    oauth2_client_token = get_oauth2_client_token(provider, user=user, refresh=True)

    if oauth2_client_token is None:
        return False, _(
            "This provider requires a service that is not yet connected to your"
            " account."
        )

    try:
        result = run_hook(
            "kadi_publish_resource",
            provider=provider,
            resource=resource,
            form_data=form_data,
            user=user,
            client=get_oauth2_client(provider),
            token=oauth2_client_token.to_authlib_token(),
            task=task,
        )
    except Exception as e:
        current_app.logger.exception(e)

        db.session.rollback()
        return False, _("The provider failed with an unexpected error.")

    if not isinstance(result, tuple) or len(result) != 2:
        return False, _("The provider is configured incorrectly.")

    return bool(result[0]), Markup(result[1])
