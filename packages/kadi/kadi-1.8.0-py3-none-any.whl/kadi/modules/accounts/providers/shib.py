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
from flask import request
from flask_babel import lazy_gettext as _l

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.conversion import recode
from kadi.lib.utils import find_dict_in_list
from kadi.lib.utils import named_tuple
from kadi.modules.accounts.models import ShibIdentity

from .core import BaseProvider


class ShibProvider(BaseProvider):
    """Shibboleth authentication provider."""

    class Meta:
        """Container to store meta class attributes."""

        provider_type = const.AUTH_PROVIDER_TYPE_SHIB
        """The type of the provider."""

        defaults = {
            "title": _l("Login with Shibboleth"),
            "default_system_role": "member",
            "activate_users": True,
            "idps": [],
            "env_encoding": "latin-1",
            "multivalue_separator": ";",
            "sp_entity_id": None,
            "sp_session_initiator": "/Shibboleth.sso/Login",
            "sp_logout_initiator": "/Shibboleth.sso/Logout",
            "idp_entity_id_attr": "Shib-Identity-Provider",
            "idp_displayname_attr": "Meta-displayName",
            "idp_support_contact_attr": "Meta-supportContact",
            "username_attr": "eppn",
            "email_attr": "mail",
            "displayname_attr": "displayName",
            "firstname_attr": "givenName",
            "lastname_attr": "sn",
        }
        """The default configuration values of the provider."""

    @classmethod
    def _get_current_env(cls):
        try:
            return request.environ
        except Exception as e:
            current_app.logger.exception(e)
            return {}

    @classmethod
    def _get_env_value(cls, key, multivalued=False):
        config = cls.get_config()
        environ = cls._get_current_env()

        env_encoding = config["env_encoding"]
        value = environ.get(key)

        if env_encoding != "utf-8":
            # Environment variables may not always be utf-8 encoded, at least those
            # coming from Apache seem to be not.
            value = recode(value, from_encoding=env_encoding)

        # We currently assume that multivalied attributes are separated via simple
        # characters or strings.
        if multivalued and value is not None:
            return value.split(config["multivalue_separator"])

        return value

    @classmethod
    def get_choices(cls):
        """Get all configured identity providers for use in a selection.

        :return: A list of tuples, each tuple containing the entity ID and display name
            of the identity provider, sorted by display name. The first entry in the
            list represents the empty default choice in a selection where both values
            are set to an empty string.
        """
        choices = [("", "")]

        if not cls.is_registered():
            return choices

        config = cls.get_config()

        for idp in config["idps"]:
            choices.append((idp.get("entity_id", ""), idp.get("name", "")))

        return sorted(choices, key=lambda x: x[1])

    @classmethod
    def get_session_initiator(cls, entity_id, target):
        """Get the configured Shibboleth session initiator.

        The session initiator is simply an URL consisting of the configured login
        endpoint of the service provider and containing the given ``entity_id`` and
        ``target`` URL as query parameters.

        :param entity_id: The entity ID of the identity provider to use for login.
        :param target: The URL to redirect to after logging in successfully.
        :return: The generated session initiator URL.
        """
        if not cls.is_registered():
            return ""

        config = cls.get_config()
        return f"{config['sp_session_initiator']}?entityID={entity_id}&target={target}"

    @classmethod
    def get_logout_initiator(cls, target):
        """Get the configured Shibboleth local logout initiator.

        The local logout initiator is simply an URL consisting of the configured logout
        endpoint of the service provider and containing the given ``target`` URL as
        query parameter.

        :param target: The URL to redirect to after logging out successfully.
        :return: The generated local logout initiator URL.
        """
        if not cls.is_registered():
            return ""

        return f"{cls.get_config()['sp_logout_initiator']}?return={target}"

    @classmethod
    def contains_valid_idp(cls):
        """Check if the current Shibboleth session contains a valid identity provider.

        In this case, valid means that the entity ID of an identity provider is
        contained in the configured list of identity providers.

        :return: ``True`` if the identity provider is valid, ``False`` otherwise.
        """
        if not cls.is_registered():
            return False

        config = cls.get_config()
        environ = cls._get_current_env()

        entity_id = environ.get(config["idp_entity_id_attr"])

        if entity_id is not None:
            idp = find_dict_in_list(config["idps"], "entity_id", entity_id)
            return idp is not None

        return False

    @classmethod
    def get_metadata(cls):
        """Get the metadata of the current Shibboleth session.

        :return: An dictionary containing the entity ID of the service provider
            (``sp_entity_id``), the entity ID of the identity provider
            (``idp_entity_id``), its display name (``idp_displayname``) and its support
            contact email address (``idp_support_contact``).
        """
        metadata = {
            "sp_entity_id": "",
            "idp_entity_id": "",
            "idp_displayname": "",
            "idp_support_contact": "",
        }

        if not cls.is_registered():
            return metadata

        config = cls.get_config()

        sp_entity_id = config["sp_entity_id"]

        if sp_entity_id is None:
            sp_entity_id = f"{current_app.base_url}/shibboleth"

        idp_support_contact = cls._get_env_value(config["idp_support_contact_attr"])

        if idp_support_contact is not None:
            # The contact email address is generally specified as a "mailto:" attribute,
            # so we try to extract the actual email address.
            parts = idp_support_contact.split(":", 1)

            if len(parts) > 1:
                idp_support_contact = parts[1]

        metadata["sp_entity_id"] = sp_entity_id
        metadata["idp_support_contact"] = idp_support_contact
        metadata["idp_entity_id"] = cls._get_env_value(config["idp_entity_id_attr"])
        metadata["idp_displayname"] = cls._get_env_value(config["idp_displayname_attr"])

        return metadata

    @classmethod
    def get_required_attributes(cls):
        """Get all required authentication attributes of the current Shibboleth session.

        :return: A dictionary containing the required keys to get as environment
            variables and their respective values. If the identity provider did not
            provide an attribute, the value will be ``None`` for the respective key.
        """
        if not cls.is_registered():
            return {}

        config = cls.get_config()

        username = cls._get_env_value(config["username_attr"])
        emails = cls._get_env_value(config["email_attr"], multivalued=True)

        return {
            config["username_attr"]: username,
            config["email_attr"]: emails[0] if emails is not None else emails,
        }

    @classmethod
    def authenticate(cls):
        """Authenticate a Shibboleth user.

        A successful authentication requires all necessary user attributes to be
        available as environment variables via a valid Shibboleth session.

        :return: An instance of :class:`.UserInfo`. If the authentication was
            successful, the contained data is a named tuple containing the username
            (``username``), email (``email``) and display name (``displayname``) of the
            user.
        """
        if not cls.is_registered():
            return cls.UserInfo(False)

        config = cls.get_config()

        username = cls._get_env_value(config["username_attr"])
        emails = cls._get_env_value(config["email_attr"], multivalued=True)

        if username is None or emails is None:
            return cls.UserInfo(False)

        displayname = cls._get_env_value(config["displayname_attr"])

        if displayname is None:
            firstnames = cls._get_env_value(config["firstname_attr"], multivalued=True)
            lastnames = cls._get_env_value(config["lastname_attr"], multivalued=True)

            if firstnames is not None and lastnames is not None:
                displayname = f"{' '.join(firstnames)} {' '.join(lastnames)}"

        if displayname is None:
            displayname = username

        shib_data = named_tuple(
            "ShibData", username=username, email=emails[0], displayname=displayname
        )
        return cls.UserInfo(True, shib_data)

    @classmethod
    def register(
        cls, *, displayname, username, email, system_role=None, apply_role_rules=True
    ):
        """Register a new Shibboleth user.

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
        :return: A new :class:`.ShibIdentity` object linked with a new user or an
            existing, updated :class:`.ShibIdentity`. Returns ``None`` if the identity
            could not be created.
        """
        if not cls.is_registered():
            return None

        identity = ShibIdentity.query.filter_by(username=username).first()

        if identity:
            identity.email = email
            db.session.commit()
            return identity

        config = cls.get_config()
        system_role = (
            system_role if system_role is not None else config["default_system_role"]
        )

        return cls.create_identity(
            ShibIdentity,
            displayname=displayname,
            system_role=system_role,
            activate_user=config["activate_users"],
            apply_role_rules=apply_role_rules,
            username=username,
            email=email,
        )
