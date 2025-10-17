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
from kadi.lib.ldap import bind
from kadi.lib.ldap import make_connection
from kadi.lib.ldap import make_server
from kadi.lib.ldap import make_upn
from kadi.lib.ldap import modify_password
from kadi.lib.ldap import search
from kadi.lib.ldap import unbind
from kadi.lib.utils import named_tuple
from kadi.modules.accounts.models import LDAPIdentity

from .core import BaseProvider


class LDAPProvider(BaseProvider):
    """LDAP authentication provider."""

    class Meta:
        """Container to store meta class attributes."""

        provider_type = const.AUTH_PROVIDER_TYPE_LDAP
        """The type of the provider."""

        defaults = {
            "title": _l("Login with LDAP"),
            "default_system_role": "member",
            "activate_users": True,
            "active_directory": False,
            "host": "",
            "port": 389,
            "encryption": "starttls",
            "validate_cert": True,
            "ciphers": None,
            "users_dn": "",
            "bind_user": None,
            "bind_pw": None,
            "username_attr": "uid",
            "email_attr": "mail",
            "displayname_attr": "displayName",
            "firstname_attr": None,
            "lastname_attr": None,
            "allow_password_change": False,
            "send_old_password": False,
        }
        """The default configuration values of the provider."""

    @classmethod
    def _make_connection(cls, bind_user=None, username=None, password=None):
        config = cls.get_config()
        encryption = config["encryption"]

        if encryption is not None:
            encryption = encryption.lower()

        server = make_server(
            config["host"],
            port=config["port"],
            use_ssl=encryption == "ldaps",
            validate_cert="REQUIRED" if config["validate_cert"] else "NONE",
            ciphers=config["ciphers"],
        )

        if server is None:
            return None

        user = None

        if bind_user is not None:
            user = bind_user
        elif username is not None:
            if config["active_directory"]:
                user = make_upn(username, config["users_dn"])
            else:
                user = f"{config['username_attr']}={username},{config['users_dn']}"

        return make_connection(
            server, user=user, password=password, use_starttls=encryption == "starttls"
        )

    @classmethod
    def _authenticate(cls, username, password):
        # Try authenticating as the user.
        connection = cls._make_connection(username=username, password=password)

        if connection is None or not bind(connection):
            return None

        # Then check if another user was configured to use for the LDAP operations.
        config = cls.get_config()
        bind_user = config["bind_user"]

        if bind_user is not None:
            unbind(connection)
            connection = cls._make_connection(
                bind_user=bind_user, password=config["bind_pw"]
            )

            if connection is None or not bind(connection):
                return None

        return connection

    @classmethod
    def allow_password_change(cls):
        if not cls.is_registered():
            return False

        return cls.get_config()["allow_password_change"]

    @classmethod
    def change_password(cls, *, username, old_password, new_password):
        if not cls.is_registered():
            return False

        config = cls.get_config()
        connection = cls._authenticate(username, old_password)

        if connection is None:
            return False

        kwargs = {}

        if config["send_old_password"]:
            kwargs["old_password"] = old_password

        result = modify_password(
            connection,
            f"{config['username_attr']}={username},{config['users_dn']}",
            new_password,
            active_directory=config["active_directory"],
            **kwargs,
        )
        unbind(connection)

        return result

    @classmethod
    def authenticate(cls, *, username, password):
        """Authenticate an LDAP user.

        :param username: The user's unique name to use for binding to the LDAP server
            and for searching their entry in the database.
        :param password: The user's password to use for binding to the LDAP server.
        :return: An instance of :class:`.UserInfo`. If the authentication was
            successful, the contained data is a named tuple containing the username
            (``username``), email (``email``) and display name (``displayname``) of the
            user.
        """
        if not cls.is_registered():
            return cls.UserInfo(False)

        connection = cls._authenticate(username, password)

        if connection is None:
            return cls.UserInfo(False)

        config = cls.get_config()

        search_filter = f"({config['username_attr']}={username})"
        attribute_map = {
            "username": config["username_attr"],
            "email": config["email_attr"],
        }

        if config["firstname_attr"] and config["lastname_attr"]:
            attribute_map["firstname"] = config["firstname_attr"]
            attribute_map["lastname"] = config["lastname_attr"]
        elif config["displayname_attr"]:
            attribute_map["displayname"] = config["displayname_attr"]

        results = search(connection, config["users_dn"], search_filter, attribute_map)
        unbind(connection)

        if results is None:
            return cls.UserInfo(False)

        username = results["username"]
        email = results["email"]

        if username is None or email is None:
            return cls.UserInfo(False)

        displayname = results.get("displayname")

        # Check if any of the optional attributes were specified to determine the
        # display name, or just fall back to the username.
        if displayname is None:
            firstname = results.get("firstname")
            lastname = results.get("lastname")

            if firstname is not None and lastname is not None:
                displayname = f"{firstname} {lastname}"

        if displayname is None:
            displayname = username

        ldap_data = named_tuple(
            "LDAPData", username=username, email=email, displayname=displayname
        )
        return cls.UserInfo(True, ldap_data)

    @classmethod
    def register(
        cls, *, displayname, username, email, system_role=None, apply_role_rules=True
    ):
        """Register a new LDAP user.

        If an identity with the given ``username`` already exists, that identity will be
        updated with the given ``email``.

        Note that this function may issue a database commit or rollback.

        :param displayname: The user's display name.
        :param username: The user's unique name.
        :param email: The user's email address.
        :param system_role: (optional) The user's system role. Defaults to the
            configured default system role.
        :param apply_role_rules: (optional) Flag indicating whether to apply all
            existing role rules to the newly registered user.
        :return: A new :class:`.LDAPIdentity` object linked with a new user or an
            existing, updated :class:`.LDAPIdentity`. Returns ``None`` if the identity
            could not be created.
        """
        if not cls.is_registered():
            return None

        identity = LDAPIdentity.query.filter_by(username=username).first()

        if identity:
            identity.email = email
            db.session.commit()
            return identity

        config = cls.get_config()
        system_role = (
            system_role if system_role is not None else config["default_system_role"]
        )

        return cls.create_identity(
            LDAPIdentity,
            displayname=displayname,
            system_role=system_role,
            activate_user=config["activate_users"],
            apply_role_rules=apply_role_rules,
            username=username,
            email=email,
        )
