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
from sqlalchemy.orm import declared_attr

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import UTCDateTime
from kadi.lib.db import generate_check_constraints
from kadi.lib.security import hash_value
from kadi.lib.security import random_bytes
from kadi.lib.utils import SimpleReprMixin
from kadi.lib.utils import utcnow


class AccessTokenMixin:
    """Mixin for SQLALchemy models representing access tokens."""

    scope = db.Column(db.Text, nullable=False, default="")
    """The scope of the access token.

    Represented as a single string defining a list of space-delimited scope values.
    """

    @declared_attr
    def user_id(cls):  # pylint: disable=no-self-argument
        """The ID of the user the access token belongs to."""
        return db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    @declared_attr
    def user(cls):  # pylint: disable=no-self-argument
        """The user relationship of the access token.

        A corresponding relationship should also be defined in the user table.
        """
        return db.relationship("User", back_populates=f"{cls.__tablename__}s")

    @property
    def is_expired(self):
        """Check if the access token is expired."""
        raise NotImplementedError


class PersonalToken(SimpleReprMixin, AccessTokenMixin, db.Model):
    """Model to represent personal tokens.

    These kind of access tokens always belong to and are managed by a certain user, so
    they may also be referred to as personal access tokens (PAT).
    """

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "name"]
        """See :class:`.SimpleReprMixin`."""

        check_constraints = {
            "name": {"length": {"max": 150}},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "personal_token"

    __table_args__ = generate_check_constraints(Meta.check_constraints)

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the personal token, auto incremented."""

    name = db.Column(db.Text, nullable=False)
    """The name of the personal token.

    Restricted to a maximum length of ``150`` characters.
    """

    token_hash = db.Column(db.Text, index=True, nullable=False)
    """The actual, hashed token value."""

    expires_at = db.Column(UTCDateTime, nullable=True)
    """The optional date and time the personal token expires in."""

    created_at = db.Column(UTCDateTime, default=utcnow, nullable=False)
    """The date and time the personal token was created at."""

    last_used = db.Column(UTCDateTime, nullable=True)
    """The date and time the personal token was last used."""

    @property
    def is_expired(self):
        """Check if the personal token is expired."""
        if self.expires_at is not None:
            return self.expires_at < utcnow()

        return False

    @staticmethod
    def new_token(include_prefix=True):
        """Create a new random token value.

        :param include_prefix: (optional) Whether to include a prefix before the actual
            token value to distinguish it with other types of access tokens.
        :return: The generated token value.
        """
        token = random_bytes()

        if include_prefix:
            return f"{const.ACCESS_TOKEN_PREFIX_PAT}{token}"

        return token

    @staticmethod
    def hash_token(token):
        """Create a secure hash of a token value.

        :param token: The token value to hash.
        :return: The calculated hash as a hexadecimal value.
        """
        prefix = const.ACCESS_TOKEN_PREFIX_PAT

        # Exclude the prefix before hashing the token, if applicable.
        if token.startswith(prefix):
            token = token[len(prefix) :]

        return hash_value(token)

    @classmethod
    def get_by_token(cls, token):
        """Get a personal token using a token value.

        :param token: The token value to search for.
        :return: The personal token or ``None``.
        """
        token_hash = cls.hash_token(token)
        return cls.query.filter_by(token_hash=token_hash).first()

    @classmethod
    def create(cls, *, user, name, scope="", expires_at=None, token=None):
        """Create a new personal token and add it to the database session.

        :param user: The user the personal token should belong to.
        :param name: The name of the personal token.
        :param scope: (optional) The scope of the personal token.
        :param expires_at: (optional) The expiration date of the personal token.
        :param token: (optional) The actual token value, which will be hashed before
            persisting. Defaults to a token value created by :meth:`new_token`.
        :return: The new :class:`PersonalToken` object.
        """
        token = token if token is not None else cls.new_token()

        personal_token = cls(
            user=user,
            name=name,
            scope=scope,
            expires_at=expires_at,
            token_hash=cls.hash_token(token),
        )
        db.session.add(personal_token)

        return personal_token
