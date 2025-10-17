# Copyright 2023 Karlsruhe Institute of Technology
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
from flask import redirect
from flask_babel import lazy_gettext as _l

import kadi.lib.constants as const
from kadi.ext.oauth import oidc_registry
from kadi.lib.oauth.utils import get_oidc_client
from kadi.lib.utils import find_dict_in_list
from kadi.lib.utils import named_tuple
from kadi.lib.web import url_for
from kadi.modules.accounts.models import OIDCIdentity

from .core import BaseProvider


class OIDCProvider(BaseProvider):
    """OpenID Connect (OIDC) authentication provider."""

    class Meta:
        """Container to store meta class attributes."""

        provider_type = const.AUTH_PROVIDER_TYPE_OIDC
        """The type of the provider."""

        defaults = {
            "title": _l("Login with OpenID Connect"),
            "default_system_role": "member",
            "activate_users": True,
            "email_confirmation_required": False,
            "providers": [],
        }
        """The default configuration values of the provider."""

    @classmethod
    def _register_oidc_client(cls, provider):
        config = cls.get_config()
        provider_config = find_dict_in_list(config["providers"], "name", provider)

        if not provider_config:
            return None

        return oidc_registry.register(
            name=provider,
            client_id=provider_config.get("client_id", ""),
            client_secret=provider_config.get("client_secret", ""),
            server_metadata_url=provider_config.get("discovery_url", ""),
            client_kwargs={"scope": "openid profile email"},
        )

    @classmethod
    def email_confirmation_required(cls):
        if not cls.is_registered():
            return False

        return cls.get_config()["email_confirmation_required"]

    @classmethod
    def allow_email_change(cls):
        if not cls.is_registered():
            return False

        return True

    @classmethod
    def get_providers(cls):
        """Get all configured OIDC providers for use in a suitable selection.

        :return: A list of dictionaries, each dictionary containing the name
            (``"name"``) and title (``"title"``) of the provider.
        """
        providers = []

        if not cls.is_registered():
            return providers

        config = cls.get_config()

        for provider in config["providers"]:
            name = provider.get("name", "")
            providers.append(
                {
                    "name": name,
                    "title": provider.get("title", name),
                    "icon": provider.get("icon"),
                }
            )

        return providers

    @classmethod
    def get_identity(cls, *, issuer, subject):
        """Get an existing OIDC identity based on the provided issuer and subject.

        :param issuer: The OIDC issuer.
        :param subject: The OIDC subject.
        :return: A :class:`.OIDCIdentity` or ``None`` if no suitable identity exists.
        """
        return OIDCIdentity.query.filter_by(issuer=issuer, subject=subject).first()

    @classmethod
    def initiate_login(cls, provider):
        """Initiate the OIDC authentication flow.

        :param provider: The name of the OIDC provider.
        :return: A response object with a corresponding redirect.
        """
        fallback_url = url_for("accounts.login", tab=const.AUTH_PROVIDER_TYPE_OIDC)

        if not cls.is_registered():
            return redirect(fallback_url)

        try:
            client = get_oidc_client(provider)
        except AttributeError:
            # Attempt to register the client if not done yet.
            client = cls._register_oidc_client(provider)

        if client is None:
            return redirect(fallback_url)

        redirect_uri = url_for("accounts.oidc_provider_authorize", provider=provider)

        try:
            return client.authorize_redirect(redirect_uri)
        except Exception as e:
            current_app.logger.exception(e)

        return redirect(fallback_url)

    @classmethod
    def authenticate(cls, *, provider):
        """Authenticate an OIDC user.

        Note that this requires an authorization code sent via the current request as
        part of the OIDC authentication flow initiated via
        :meth:`.OIDCProvider.initiate_login`.

        :param provider: The name of the OIDC provider.
        :return: An instance of :class:`.UserInfo`. If the authentication was
            successful, the contained data is a named tuple containing the issuer
            (``issuer``), subject (``subject``), username (``username``), email
            (``email``), email confirmation flag (``email_confirmed``) and display name
            (``displayname``) of the user.
        """
        if not cls.is_registered():
            return cls.UserInfo(False)

        try:
            client = get_oidc_client(provider)
        except AttributeError:
            # Attempt to register the client if not done yet.
            client = cls._register_oidc_client(provider)

        if client is None:
            return cls.UserInfo(False)

        try:
            token_data = client.authorize_access_token()
            id_token = token_data["userinfo"]
        except Exception as e:
            current_app.logger.exception(e)
            return cls.UserInfo(False)

        username = id_token.get("preferred_username", "")
        email = id_token.get("email", "")
        email_confirmed = id_token.get("email_verified", False)
        displayname = id_token.get("name")

        if displayname is None:
            firstname = id_token.get("given_name", "")
            lastname = id_token.get("family_name", "")

            if firstname or lastname:
                displayname = f"{firstname} {lastname}".strip()
            else:
                displayname = username

        oidc_data = named_tuple(
            "OIDCData",
            issuer=id_token["iss"],
            subject=id_token["sub"],
            username=username,
            email=email,
            email_confirmed=email_confirmed,
            displayname=displayname,
        )
        return cls.UserInfo(True, oidc_data)

    @classmethod
    def register(
        cls,
        *,
        displayname,
        username,
        email,
        email_confirmed,
        issuer,
        subject,
        system_role=None,
        apply_role_rules=True,
    ):
        """Register a new OIDC user.

        Note that this function may issue a database commit or rollback.

        :param displayname: The user's display name.
        :param username: The user's unique name.
        :param email: The user's email address.
        :param email_confirmed: Flag indicating whether the user's email address should
            be marked as confirmed.
        :param issuer: The OIDC issuer.
        :param subject: The OIDC subject.
        :param system_role: (optional) The user's system role. Defaults to the
            configured default system role.
        :param apply_role_rules: (optional) Flag indicating whether to apply all
            existing role rules to the newly registered user.
        :return: A new :class:`.OIDCIdentity` object linked with a new user or ``None``
            if the identity could not be created.
        """
        if not cls.is_registered():
            return None

        config = cls.get_config()
        system_role = (
            system_role if system_role is not None else config["default_system_role"]
        )

        return cls.create_identity(
            OIDCIdentity,
            displayname=displayname,
            system_role=system_role,
            activate_user=config["activate_users"],
            apply_role_rules=apply_role_rules,
            username=username,
            email=email,
            email_confirmed=email_confirmed,
            issuer=issuer,
            subject=subject,
        )
