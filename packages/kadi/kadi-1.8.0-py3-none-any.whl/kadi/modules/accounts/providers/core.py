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
from sqlalchemy.exc import IntegrityError

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.permissions.core import set_system_role
from kadi.lib.permissions.tasks import start_apply_role_rules_task
from kadi.lib.utils import get_class_by_name
from kadi.modules.accounts.models import User
from kadi.modules.accounts.models import UserState


class BaseProvider:
    """Base class for authentication providers.

    Note that the function :func:`init_auth_providers` needs to be called beforehand to
    initialize the application for use with the configured authentication providers.
    """

    class Meta:
        """Container to store meta class attributes."""

        provider_type = None
        """The type of a provider."""

        defaults = {}
        """The default configuration values of a provider.

        Each provider should at least specify a ``title`` alongside all other
        provider-specific configuration.
        """

    class UserInfo:
        """Wrapper class to store user authentication information.

        :param is_authenticated: Flag to indicate if the represented user is
            authenticated or not.
        :param data: (optional) The wrapped user data. This should generally be an
            object-like type representing information about the authenticated user.
        """

        def __init__(self, is_authenticated, data=None):
            self.is_authenticated = is_authenticated
            self.data = data

    @classmethod
    def create_identity(
        cls,
        identity_model,
        *,
        displayname,
        system_role,
        activate_user=True,
        apply_role_rules=True,
        **kwargs,
    ):
        r"""Create a new user and a corresponding identity.

        The latest identity of the user will be set to the newly created one
        automatically. Additionally, all existing role rules will be applied to the
        newly created user in a background task.

        Note that this function issues a database commit or rollback.

        :param identity_model: The identity model to use for creating the user's
            identity.
        :param displayname: The display name of the user. May be truncated if it exceeds
            the maximum allowed length.
        :param system_role: The system role of the user.
        :param activate_user: (optional) Flag indicating whether the newly registered
            user should be activated automatically.
        :param apply_role_rules: (optional) Flag indicating whether to apply all
            existing role rules to the newly registered user.
        :param \**kwargs: Additional keyword arguments to pass to the identity model's
            ``create`` method.
        :return: The newly created identity or ``None`` if it could not be created.
        """
        if activate_user:
            user_state = UserState.ACTIVE
        else:
            user_state = UserState.INACTIVE

        # Ensure the provided display name does not exceed the maximum length, as it may
        # be provided by an external service as-is.
        max_len = User.Meta.check_constraints["displayname"]["length"]["max"]
        user = User.create(displayname=displayname[:max_len], state=user_state)

        if not set_system_role(user, system_role):
            db.session.rollback()
            return None

        identity = identity_model.create(user=user, **kwargs)

        try:
            db.session.flush()
        except IntegrityError:
            db.session.rollback()
            return None

        user.identity = identity
        db.session.commit()

        if apply_role_rules:
            start_apply_role_rules_task(user=user)

        return identity

    @classmethod
    def is_registered(cls):
        """Check if a provider is registered in the application.

        :return: ``True`` if the provider is registered, ``False`` otherwise.
        """
        return cls.Meta.provider_type in current_app.config["AUTH_PROVIDERS"]

    @classmethod
    def get_config(cls):
        """Get a provider's config from the current application object.

        :return: The provider's configuration as dictionary.
        """
        return current_app.config["AUTH_PROVIDERS"].get(cls.Meta.provider_type)

    @classmethod
    def email_confirmation_required(cls):
        """Check if a provider requires email confirmation.

        By default, this is assumed to not be the case for all identity providers.

        :return: ``True`` if the provider requires email confirmation, ``False``
            otherwise.
        """
        return False

    @classmethod
    def allow_email_change(cls):
        """Check if a provider supports changing emails.

        By default, this is assumed to not be the case for all identity providers.

        :return: ``True`` if the provider supports changing passwords, ``False``
            otherwise.
        """
        return False

    @classmethod
    def allow_password_change(cls):
        """Check if a provider supports changing passwords.

        By default, this is assumed to not be the case for all identity providers.

        :return: ``True`` if the provider supports changing passwords, ``False``
            otherwise.
        """
        return False

    @classmethod
    def change_password(cls, *, username, old_password, new_password):
        """Change a password of an existing user if supported by a provider.

        :param username: The unique username of the user.
        :param old_password: The current password of the user.
        :param new_password: The new password of the user.
        :return: ``True`` if the password change was successful, ``False`` otherwise.
        """
        return False


def init_auth_providers(app):
    """Initialize all authentication providers for use in the application.

    Rebuilds the ``AUTH_PROVIDERS`` specified in the application's configuration to use
    a dictionary, which will be updated with the default values for each provider,
    wherever applicable, and also includes the following additional class references for
    convenience:

    * ``"provider_class"``: A reference to the provider class.
    * ``"identity_class"``: A reference to the identity class.
    * ``"form_class"``: A reference to the form class.

    :param app: The application object.
    """
    auth_providers = app.config["AUTH_PROVIDERS"]
    app.config["AUTH_PROVIDERS"] = {}

    for provider_config in auth_providers:
        provider_type = provider_config.get("type")

        if provider_type not in const.AUTH_PROVIDER_TYPES:
            app.logger.warn(
                f"The authentication provider type '{provider_type}' does not exist."
            )
            continue

        # Add the class references to the configuration.
        auth_classes = const.AUTH_PROVIDER_TYPES[provider_type]

        for attr in ["provider", "identity", "form"]:
            provider_config[f"{attr}_class"] = get_class_by_name(auth_classes[attr])

        # Set the default values for the provider.
        for key, value in provider_config["provider_class"].Meta.defaults.items():
            if key not in provider_config:
                provider_config[key] = value

        app.config["AUTH_PROVIDERS"][provider_type] = provider_config


def get_auth_provider(name):
    """Get the provider class of an authentication provider by its name.

    :param name: The name of the authentication provider.
    :return: The authentication provider class or ``None`` if no provider with the given
        name exists.
    """
    provider_config = current_app.config["AUTH_PROVIDERS"].get(name)

    if provider_config is not None:
        return provider_config["provider_class"]

    return None
