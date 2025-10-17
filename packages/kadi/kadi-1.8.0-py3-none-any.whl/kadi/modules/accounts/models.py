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
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.config.core import MISSING
from kadi.lib.config.core import get_user_config
from kadi.lib.config.core import set_user_config
from kadi.lib.db import SimpleTimestampMixin
from kadi.lib.db import UTCDateTime
from kadi.lib.db import generate_check_constraints
from kadi.lib.db import unique_constraint
from kadi.lib.security import encode_jwt
from kadi.lib.utils import SimpleReprMixin
from kadi.lib.utils import StringEnum
from kadi.lib.utils import utcnow
from kadi.modules.sysadmin.utils import get_legals_modification_date
from kadi.modules.sysadmin.utils import legals_acceptance_required


class UserState(StringEnum):
    """String enum containing all possible state values for users.

    * ``ACTIVE``: For users that are active.
    * ``INACTIVE``: For users that have been marked as (temporarily) inactive.
    * ``DELETED``: For users that have been marked for deletion.
    """

    __values__ = [const.MODEL_STATE_ACTIVE, "inactive", const.MODEL_STATE_DELETED]


class User(SimpleReprMixin, SimpleTimestampMixin, UserMixin, db.Model):
    """Model to represent users.

    In general, every resource that a user "owns" should be linked to this model. Each
    user can also potentially have multiple identities associated with it, all pointing
    to the same user.
    """

    class Meta:
        """Container to store meta class attributes."""

        representation = [
            "id",
            "displayname",
            "latest_identity_id",
            "is_sysadmin",
            "new_user_id",
            "state",
        ]
        """See :class:`.SimpleReprMixin`."""

        timestamp_exclude = [
            "identities",
            "records",
            "record_links",
            "files",
            "temporary_files",
            "uploads",
            "collections",
            "templates",
            "groups",
            "workflows",
            "revisions",
            "favorites",
            "saved_searches",
            "config_items",
            "tasks",
            "notifications",
            "personal_tokens",
            "oauth2_client_tokens",
            "oauth2_server_clients",
            "oauth2_server_tokens",
            "oauth2_server_auth_codes",
            "roles",
        ]
        """See :class:`.BaseTimestampMixin`."""

        check_constraints = {
            "displayname": {"length": {"max": 150}},
            "orcid": {"length": {"max": 19}},
            "about": {"length": {"max": 10_000}},
            "state": {"values": UserState.__values__},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "user"

    __table_args__ = (
        *generate_check_constraints(Meta.check_constraints),
        # Defined here so Alembic can resolve the cyclic user/identity reference.
        db.ForeignKeyConstraint(
            ["latest_identity_id"], ["identity.id"], use_alter=True
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the user, auto incremented."""

    displayname = db.Column(db.Text, nullable=False)
    """The display name of the user.

    Restricted to a maximum length of ``150`` characters.
    """

    orcid = db.Column(db.Text, nullable=True)
    """The optional ORCID iD of the user.

    Restricted to a maximum length of ``19`` characters.
    """

    about = db.Column(db.Text, default="", nullable=False)
    """Additional user information.

    Restricted to a maximum length of ``10_000`` characters.
    """

    image_name = db.Column(UUID(as_uuid=True), nullable=True)
    """The optional identifier of a user's profile image."""

    email_is_private = db.Column(db.Boolean, default=True, nullable=False)
    """Flag indicating whether a user's identities email addresses are private."""

    latest_identity_id = db.Column(db.Integer, nullable=True)
    """The ID of the latest :class:`.Identity` the user logged in with."""

    is_sysadmin = db.Column(db.Boolean, default=False, nullable=False)
    """Flag indicating whether a user is a sysadmin."""

    legals_accepted = db.Column(UTCDateTime, nullable=True)
    """Flag indicating if and when a user accepted the legal notices, if configured."""

    new_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    """The ID of a :class:`.User` the current user was merged with."""

    state = db.Column(db.Text, index=True, nullable=False)
    """The state of the user.

    See :class:`.UserState`.
    """

    identity = db.relationship("Identity", foreign_keys="User.latest_identity_id")

    identities = db.relationship(
        "Identity",
        lazy="dynamic",
        foreign_keys="Identity.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    records = db.relationship("Record", lazy="dynamic", back_populates="creator")

    record_links = db.relationship(
        "RecordLink", lazy="dynamic", back_populates="creator"
    )

    files = db.relationship("File", lazy="dynamic", back_populates="creator")

    temporary_files = db.relationship(
        "TemporaryFile",
        lazy="dynamic",
        back_populates="creator",
        cascade="all, delete-orphan",
    )

    uploads = db.relationship("Upload", lazy="dynamic", back_populates="creator")

    collections = db.relationship(
        "Collection", lazy="dynamic", back_populates="creator"
    )

    templates = db.relationship("Template", lazy="dynamic", back_populates="creator")

    groups = db.relationship("Group", lazy="dynamic", back_populates="creator")

    workflows = db.relationship(
        "Workflow",
        lazy="dynamic",
        back_populates="creator",
        cascade="all, delete-orphan",
    )

    revisions = db.relationship("Revision", lazy="dynamic", back_populates="user")

    favorites = db.relationship(
        "Favorite", lazy="dynamic", back_populates="user", cascade="all, delete-orphan"
    )

    saved_searches = db.relationship(
        "SavedSearch",
        lazy="dynamic",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    config_items = db.relationship(
        "ConfigItem",
        lazy="dynamic",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    tasks = db.relationship(
        "Task", lazy="dynamic", back_populates="creator", cascade="all, delete-orphan"
    )

    notifications = db.relationship(
        "Notification",
        lazy="dynamic",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    personal_tokens = db.relationship(
        "PersonalToken",
        lazy="dynamic",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    oauth2_client_tokens = db.relationship(
        "OAuth2ClientToken",
        lazy="dynamic",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    oauth2_server_clients = db.relationship(
        "OAuth2ServerClient",
        lazy="dynamic",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    oauth2_server_tokens = db.relationship(
        "OAuth2ServerToken",
        lazy="dynamic",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    oauth2_server_auth_codes = db.relationship(
        "OAuth2ServerAuthCode",
        lazy="dynamic",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    roles = db.relationship(
        "Role", secondary="user_role", lazy="dynamic", back_populates="users"
    )

    @property
    def initials(self):
        """Get the initials of a user based on their display name."""
        names = self.displayname.split(" ")
        initials = names[0][0]

        if len(names) > 1:
            initials += names[-1][0]

        return initials.upper()

    @property
    def is_merged(self):
        """Check if a user was merged."""
        return self.new_user_id is not None

    @property
    def needs_legals_acceptance(self):
        """Check if a user needs to accept the legal notices.

        This is the case if accepting the legal notices is required and the user did not
        accept them (or changes to them) yet.
        """

        # Check if accepting the legal notices is required at all.
        if not legals_acceptance_required():
            return False

        # Check if the user never accepted the legal notices before.
        if self.legals_accepted is None:
            return True

        # Check if there is a valid modification date of the legal notices. If so,
        # compare this date to the date of acceptance.
        modification_date = get_legals_modification_date()

        if modification_date is not None:
            return self.legals_accepted < modification_date

        # Otherwise, we consider the legal notices as accepted.
        return False

    @classmethod
    def create(cls, *, displayname, state=UserState.ACTIVE):
        """Create a new user and add it to the database session.

        :param displayname: The display name of the user.
        :param state: (optional) The state of the user.
        :return: The new :class:`User` object.
        """
        user = cls(displayname=displayname, state=state)
        db.session.add(user)

        return user

    def get_user_id(self):
        """Get the ID of this user.

        Required for the implementation of the OAuth2 server.
        """
        return self.id

    def accept_legals(self):
        """Accept the legal notices for this user.

        Automatically sets the date of acceptance to the current date.
        """
        self.legals_accepted = utcnow()

    def get_config(self, key, default=MISSING, decrypt=False):
        """Get the value of a user-specific config item from the database.

        Convenience method that wraps :func:`kadi.lib.config.core.get_user_config` with
        the user set accordingly.
        """
        return get_user_config(key, user=self, default=default, decrypt=decrypt)

    def set_config(self, key, value, encrypt=False):
        """Set the value of a user-specific config item in the database.

        Convenience method that wraps :func:`kadi.lib.config.core.set_user_config` with
        the user set accordingly.
        """
        return set_user_config(key, value, user=self, encrypt=encrypt)


class Identity(SimpleReprMixin, SimpleTimestampMixin, db.Model):
    """Model to represent base identities.

    This model uses its :attr:`type` column to specify different types of identities.
    Each specific identity, i.e. each subclass of this model, needs at least a unique
    ``username`` and an ``email`` column.
    """

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "type"]
        """See :class:`.SimpleReprMixin`."""

        common_constraints = {
            "username": {"length": {"min": 3, "max": 50}},
            "email": {"length": {"max": 256}},
        }
        """Common check constraints for the minimum required identity attributes.

        These are useful for identities where the underlying accounts are user-supplied
        via a corresponding registration form.
        """

    __tablename__ = "identity"

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the identity, auto incremented."""

    # Needs to be nullable because of the "post_update" in the "user" relationship.
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    """The ID of the :class:`.User` the identity belongs to."""

    type = db.Column(db.Text, nullable=False)
    """The identity type.

    Used by SQLAlchemy to distinguish between different identity types and to
    automatically select from the correct identity table using joined table inheritance.
    """

    # "post_update" is needed because otherwise deleting a user/identity can cause
    # issues due to the cyclic user/identity relationship.
    user = db.relationship(
        "User",
        foreign_keys="Identity.user_id",
        back_populates="identities",
        post_update=True,
    )

    __mapper_args__ = {"polymorphic_identity": "identity", "polymorphic_on": type}

    @property
    def email_confirmed(self):
        """Check if an identity's email address is confirmed.

        By default, this is assumed to be the case for all concrete identity types.
        """
        return True

    @property
    def needs_email_confirmation(self):
        """Check if an identity's email address needs to be confirmed.

        By default, this is assumed to not be the case for all concrete identity types.
        """
        return False

    def get_email_confirmation_token(self, expires_in, email=None):
        """Create a new JSON web token used for email confirmation.

        :param expires_in: The time in seconds the token will expire in.
        :param email: (optional) An email to include in the payload of the token, which
            can be used to change an identity's email on confirmation. Defaults to the
            identity's current email.
        :return: The encoded token.
        """
        return encode_jwt(
            {
                "type": const.JWT_TYPE_EMAIL_CONFIRMATION,
                "email": email if email is not None else self.email,
                "id": self.id,
            },
            expires_in=expires_in,
        )


class LocalIdentity(Identity):
    """Model to represent local identities."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "username", "email"]
        """See :class:`.SimpleReprMixin`."""

        identity_type = {
            "type": const.AUTH_PROVIDER_TYPE_LOCAL,
            "name": _l("Local"),
        }
        """The type and full name of the identity."""

        check_constraints = Identity.Meta.common_constraints
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "local_identity"

    __table_args__ = generate_check_constraints(Meta.check_constraints)

    __mapper_args__ = {"polymorphic_identity": Meta.identity_type["type"]}

    id = db.Column(db.Integer, db.ForeignKey("identity.id"), primary_key=True)
    """The ID of the identity and of the associated base identity."""

    username = db.Column(db.Text, index=True, unique=True, nullable=False)
    """The unique username of the identity.

    Restricted to a minimum length of ``3`` and a maximum length of ``50`` characters.
    """

    email = db.Column(db.Text, nullable=False)
    """The email address of the identity.

    Restricted to a maximum length of ``256`` characters.
    """

    password_hash = db.Column(db.Text, nullable=False)
    """Hashed password using scrypt and a salt value of ``16`` chars."""

    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    """Indicates whether the user's email has been confirmed."""

    @property
    def needs_email_confirmation(self):
        from .providers.local import LocalProvider

        return LocalProvider.email_confirmation_required() and not self.email_confirmed

    @classmethod
    def create(cls, *, user, username, email, password):
        """Create a new local identity and add it to the database session.

        :param user: The user the identity should belong to.
        :param username: The identity's unique username.
        :param email: The identity's email.
        :param password: The identity's password, which will be hashed securely before
            persisting.
        :return: The new :class:`LocalIdentity` object.
        """
        local_identity = cls(user=user, username=username, email=email)

        local_identity.set_password(password)
        db.session.add(local_identity)

        return local_identity

    def set_password(self, password):
        """Set an identity's password.

        :param password: The password, which will be hashed securely before persisting.
        """
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password):
        """Check if an identity's password matches the given password.

        The given password will be hashed and checked against the stored password hash.
        Note that if the current password hash does not match the hash method used by
        :meth:`set_password`, the password hash will be updated accordingly.

        :param password: The password to check.
        :return: True if the passwords match, False otherwise.
        """
        if check_password_hash(self.password_hash, password):
            method = self.password_hash.split("$", 1)[0]

            if not method.startswith("scrypt:"):
                self.set_password(password)

            return True

        return False

    def get_password_reset_token(self, expires_in):
        """Create a new JSON web token used for password resets.

        :param expires_in: The time in seconds the token will expire in.
        :return: The encoded token.
        """
        return encode_jwt(
            {
                "type": const.JWT_TYPE_PASSWORD_RESET,
                "id": self.id,
            },
            expires_in=expires_in,
        )


class LDAPIdentity(Identity):
    """Model to represent LDAP identities."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "username", "email"]
        """See :class:`.SimpleReprMixin`."""

        identity_type = {
            "type": const.AUTH_PROVIDER_TYPE_LDAP,
            "name": "LDAP",
        }
        """The type and full name of the identity."""

    __tablename__ = "ldap_identity"

    __mapper_args__ = {"polymorphic_identity": Meta.identity_type["type"]}

    id = db.Column(db.Integer, db.ForeignKey("identity.id"), primary_key=True)
    """The ID of the identity and of the associated base identity."""

    username = db.Column(db.Text, index=True, unique=True, nullable=False)
    """The unique username of the identity."""

    email = db.Column(db.Text, nullable=False)
    """The email address of the identity."""

    @classmethod
    def create(cls, *, user, username, email):
        """Create a new LDAP identity and add it to the database session.

        :param user: The user the identity should belong to.
        :param username: The identity's unique username.
        :param email: The identity's email.
        :return: The new :class:`LDAPIdentity` object.
        """
        ldap_identity = cls(user=user, username=username, email=email)
        db.session.add(ldap_identity)

        return ldap_identity


class OIDCIdentity(Identity):
    """Model to represent OpenID Connect (OIDC) identities."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "username", "email", "issuer"]
        """See :class:`.SimpleReprMixin`."""

        identity_type = {
            "type": const.AUTH_PROVIDER_TYPE_OIDC,
            "name": "OpenID Connect",
        }
        """The type and full name of the identity."""

        check_constraints = Identity.Meta.common_constraints
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "oidc_identity"

    __table_args__ = (
        *generate_check_constraints(Meta.check_constraints),
        unique_constraint(__tablename__, "issuer", "subject"),
    )

    __mapper_args__ = {"polymorphic_identity": Meta.identity_type["type"]}

    id = db.Column(db.Integer, db.ForeignKey("identity.id"), primary_key=True)
    """The ID of the identity and of the associated base identity."""

    username = db.Column(db.Text, index=True, unique=True, nullable=False)
    """The unique username of the identity."""

    email = db.Column(db.Text, nullable=False)
    """The email address of the identity.

    Restricted to a maximum length of ``256`` characters.
    """

    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    """Indicates whether the user's email has been confirmed."""

    issuer = db.Column(db.Text, nullable=False)
    """The OIDC issuer."""

    subject = db.Column(db.Text, nullable=False)
    """The OIDC subject."""

    @property
    def needs_email_confirmation(self):
        from .providers.oidc import OIDCProvider

        return OIDCProvider.email_confirmation_required() and not self.email_confirmed

    @classmethod
    def create(cls, *, user, username, email, email_confirmed, issuer, subject):
        """Create a new OIDC identity and add it to the database session.

        :param user: The user the identity should belong to.
        :param username: The identity's unique username.
        :param email: The identity's email.
        :param email_confirmed: Flag indicating whether the user's email address should
            be marked as confirmed.
        :param issuer: The OIDC issuer.
        :param subject: The OIDC subject.
        :return: The new :class:`OIDCIdentity` object.
        """
        oidc_identity = cls(
            user=user,
            username=username,
            email=email,
            email_confirmed=email_confirmed,
            issuer=issuer,
            subject=subject,
        )
        db.session.add(oidc_identity)

        return oidc_identity


class ShibIdentity(Identity):
    """Model to represent Shibboleth identities."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "username", "email"]
        """See :class:`.SimpleReprMixin`."""

        identity_type = {
            "type": const.AUTH_PROVIDER_TYPE_SHIB,
            "name": "Shibboleth",
        }
        """The type and full name of the identity."""

    __tablename__ = "shib_identity"

    __mapper_args__ = {"polymorphic_identity": Meta.identity_type["type"]}

    id = db.Column(db.Integer, db.ForeignKey("identity.id"), primary_key=True)
    """The ID of the identity and of the associated base identity."""

    username = db.Column(db.Text, index=True, unique=True, nullable=False)
    """The unique username of the identity."""

    email = db.Column(db.Text, nullable=False)
    """The email address of the identity."""

    @classmethod
    def create(cls, *, user, username, email):
        """Create a new Shibboleth identity and add it to the database session.

        :param user: The user the identity should belong to.
        :param username: The identity's unique username.
        :param email: The identity's email.
        :return: The new :class:`ShibIdentity` object.
        """
        shib_identity = cls(user=user, username=username, email=email)
        db.session.add(shib_identity)

        return shib_identity


# Auxiliary table for user roles.
db.Table(
    "user_role",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id"), primary_key=True),
)
