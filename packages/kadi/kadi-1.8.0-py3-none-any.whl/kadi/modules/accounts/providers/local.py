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
from flask_babel import lazy_gettext as _l

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.modules.accounts.models import LocalIdentity

from .core import BaseProvider


class LocalProvider(BaseProvider):
    """Local authentication provider."""

    class Meta:
        """Container to store meta class attributes."""

        provider_type = const.AUTH_PROVIDER_TYPE_LOCAL
        """The type of the provider."""

        defaults = {
            "title": _l("Login with credentials"),
            "default_system_role": "member",
            "activate_users": True,
            "email_confirmation_required": False,
            "allow_registration": False,
        }
        """The default configuration values of the provider."""

    @classmethod
    def _authenticate(cls, username, password):
        identity = LocalIdentity.query.filter_by(username=username).first()

        if identity and identity.check_password(password):
            return identity

        return None

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
    def allow_password_change(cls):
        if not cls.is_registered():
            return False

        return True

    @classmethod
    def change_password(cls, *, username, old_password, new_password):
        """Change a password of an existing local user.

        Note that this function may issue a database commit.

        See also :meth:`.BaseProvider.change_password`.
        """
        if not cls.is_registered():
            return False

        identity = cls._authenticate(username, old_password)

        if identity is not None:
            identity.set_password(new_password)
            db.session.commit()
            return True

        return False

    @classmethod
    def allow_registration(cls):
        """Check if this provider allows registration of new users.

        :return: ``True`` if registration is allowed, ``False`` otherwise.
        """
        if not cls.is_registered():
            return False

        return cls.get_config()["allow_registration"]

    @classmethod
    def authenticate(cls, *, username, password):
        """Authenticate a local user.

        Note that this function may issue a database commit.

        :param username: The user's unique name to search in the local database.
        :param password: The user's password to call
            :meth:`.LocalIdentity.check_password` with.
        :return: An instance of :class:`.UserInfo`. If the authentication was
            successful, the contained data is the user's existing
            :class:`.LocalIdentity`.
        """
        if not cls.is_registered():
            return cls.UserInfo(False)

        identity = cls._authenticate(username, password)

        if identity is not None:
            # Persist the potentially updated password hash.
            db.session.commit()
            return cls.UserInfo(True, identity)

        return cls.UserInfo(False)

    @classmethod
    def register(
        cls,
        *,
        displayname,
        username,
        email,
        password,
        system_role=None,
        apply_role_rules=True,
    ):
        """Register a new local user.

        Note that this function may issue a database commit or rollback.

        :param displayname: The user's display name.
        :param username: The user's unique name.
        :param email: The user's email address.
        :param password: The user's password.
        :param system_role: (optional) The user's system role. Defaults to the
            configured default system role.
        :param apply_role_rules: (optional) Flag indicating whether to apply all
            existing role rules to the newly registered user.
        :return: A new :class:`.LocalIdentity` object linked with a new user or ``None``
            if the identity could not be created.
        """
        if not cls.is_registered():
            return None

        config = cls.get_config()
        system_role = (
            system_role if system_role is not None else config["default_system_role"]
        )

        return cls.create_identity(
            LocalIdentity,
            displayname=displayname,
            system_role=system_role,
            activate_user=config["activate_users"],
            apply_role_rules=apply_role_rules,
            username=username,
            email=email,
            password=password,
        )
