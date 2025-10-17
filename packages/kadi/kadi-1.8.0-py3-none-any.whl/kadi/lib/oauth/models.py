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
import secrets
from time import time

from authlib.integrations.sqla_oauth2 import OAuth2AuthorizationCodeMixin
from authlib.integrations.sqla_oauth2 import OAuth2ClientMixin
from authlib.integrations.sqla_oauth2 import OAuth2TokenMixin
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy_utils.types.encrypted.encrypted_type import StringEncryptedType

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.api.models import AccessTokenMixin
from kadi.lib.db import KadiAesEngine
from kadi.lib.db import SimpleTimestampMixin
from kadi.lib.db import UTCDateTime
from kadi.lib.db import unique_constraint
from kadi.lib.security import hash_value
from kadi.lib.security import random_bytes
from kadi.lib.utils import SimpleReprMixin
from kadi.lib.utils import utcnow


class OAuth2ClientToken(SimpleReprMixin, db.Model):
    """Model to represent OAuth2 client tokens.

    Note that this model uses encrypted fields and can potentially raise a
    :class:`.KadiDecryptionKeyError` when a value cannot be decrypted.
    """

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "name"]
        """See :class:`.SimpleReprMixin`."""

    __tablename__ = "oauth2_client_token"

    __table_args__ = (unique_constraint(__tablename__, "user_id", "name"),)

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the client token, auto incremented."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` the client token belongs to."""

    name = db.Column(db.Text, nullable=False)
    """The name of the client token.

    Currently always refers to the name of a specific OAuth2 provider.
    """

    access_token = db.Column(
        StringEncryptedType(
            type_in=db.Text, engine=KadiAesEngine, key=KadiAesEngine.get_secret_key
        ),
        nullable=False,
    )
    """The actual access token value, stored encrypted."""

    refresh_token = db.Column(
        StringEncryptedType(
            type_in=db.Text, engine=KadiAesEngine, key=KadiAesEngine.get_secret_key
        ),
        nullable=True,
    )
    """The optional refresh token value, stored encrypted."""

    expires_at = db.Column(UTCDateTime, nullable=True)
    """The optional expiration date and time of the access token."""

    user = db.relationship("User", back_populates="oauth2_client_tokens")

    @property
    def is_expired(self):
        """Check if the access token is expired."""
        if self.expires_at is not None:
            return self.expires_at < utcnow()

        return False

    @classmethod
    def create(cls, *, user, name, access_token, refresh_token=None, expires_at=None):
        """Create a new OAuth2 client token and add it to the database session.

        :param user: The user the client token should belong to.
        :param name: The name of the client token.
        :param access_token: The actual access token value.
        :param refresh_token: (optional) The refresh token value.
        :param expires_at: (optional) The expiration date and time of the access token.
        :return: The new :class:`.OAuth2ClientToken` object.
        """
        oauth2_client_token = cls(
            user=user,
            name=name,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        db.session.add(oauth2_client_token)

        return oauth2_client_token

    def to_authlib_token(self):
        """Convert the client token to a format usable by an Authlib client.

        :return: A dictionary representation of the client token.
        """
        expires_at = None

        if self.expires_at is not None:
            expires_at = int(self.expires_at.timestamp())

        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": expires_at,
            "token_type": const.OAUTH_TOKEN_TYPE,
        }


class OAuth2ServerClient(
    SimpleReprMixin, SimpleTimestampMixin, OAuth2ClientMixin, db.Model
):
    """Model to represent registered OAuth2 clients/applications."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "client_id", "client_name"]
        """See :class:`.SimpleReprMixin`."""

    __tablename__ = "oauth2_server_client"

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the client, auto incremented."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` who created the client."""

    client_id = db.Column(db.Text, unique=True, nullable=False)
    """The OAuth2 client ID."""

    client_secret = db.Column(db.Text, nullable=False)
    """The OAuth2 client secret.

    Note that only a hash of the actual client secret value is stored.
    """

    _client_metadata = db.Column("client_metadata", JSONB, nullable=False)
    """Additional metadata of the client."""

    user = db.relationship("User", back_populates="oauth2_server_clients")

    oauth2_server_tokens = db.relationship(
        "OAuth2ServerToken",
        lazy="dynamic",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    oauth2_server_auth_codes = db.relationship(
        "OAuth2ServerAuthCode",
        lazy="dynamic",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    @property
    def client_metadata(self):
        """Get the additional metadata of this client."""
        return self._client_metadata

    @staticmethod
    def new_client_secret():
        """Create a new random client secret.

        :return: The generated client secret.
        """
        return random_bytes(num_bytes=32)

    @staticmethod
    def hash_client_secret(client_secret):
        """Create a secure hash of a client secret.

        :param client_secret: The client secret to hash.
        :return: The calculated hash as a hexadecimal value.
        """
        return hash_value(client_secret)

    @classmethod
    def create(
        cls,
        *,
        user,
        client_name,
        client_uri,
        redirect_uris,
        scope="",
        client_secret=None,
    ):
        """Create a new OAuth2 client and add it to the database session.

        :param user: The user the client should belong to.
        :param client_name: The name of the client. Will be stored as part of the client
            metadata.
        :param client_uri: The website of the client. Will be stored as part of the
            client metadata.
        :param redirect_uris: A list of allowed redirect URIs. Will be stored as part of
            the client metadata.
        :param scope: (optional) The scope of the client as a single string defining a
            list of space-delimited scope values. Will be stored as part of the client
            metadata.
        :param client_secret: (optional) The client secret, which will be hashed before
            persisting. Defaults to a client secret created by
            :meth:`new_client_secret`.
        :return: The new :class:`.OAuth2ServerClient` object.
        """
        client_secret = (
            client_secret if client_secret is not None else cls.new_client_secret()
        )

        oauth2_client = cls(
            user=user,
            client_id=random_bytes(num_bytes=16),
            client_secret=cls.hash_client_secret(client_secret),
            client_id_issued_at=int(time()),
        )
        db.session.add(oauth2_client)

        client_metadata = {
            "client_name": client_name,
            "client_uri": client_uri,
            "redirect_uris": redirect_uris,
            "scope": scope,
            "token_endpoint_auth_method": const.OAUTH_TOKEN_ENDPOINT_AUTH_METHOD,
            "grant_types": [
                const.OAUTH_GRANT_AUTH_CODE,
                const.OAUTH_GRANT_REFRESH_TOKEN,
            ],
            "response_types": const.OAUTH_RESPONSE_TYPE,
        }
        oauth2_client.set_client_metadata(client_metadata)

        return oauth2_client

    def set_client_metadata(self, value):
        """Set the additional metadata of this client.

        :param value: The metadata as a JSON serializable dictionary.
        """
        self._client_metadata = value

    def update_client_metadata(self, **kwargs):
        r"""Update the additional metadata of this client.

        :param \**kwargs: JSON serializable keyword arguments to update the metadata
            with.
        """
        for key, value in kwargs.items():
            if key not in self._client_metadata or self._client_metadata[key] != value:
                self._client_metadata.update(kwargs)
                # Let SQLAlchemy know about the change, as it won't be persisted
                # otherwise.
                flag_modified(self, "_client_metadata")
                return

    def check_client_secret(self, client_secret):
        """Compare the client secret of this client with a given client secret.

        :param client_secret: The client secret to compare with, which will be hashed
            before comparing.
        """
        return secrets.compare_digest(
            self.client_secret, self.hash_client_secret(client_secret)
        )


class OAuth2ServerToken(SimpleReprMixin, AccessTokenMixin, OAuth2TokenMixin, db.Model):
    """Model to represent OAuth2 server tokens."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "client_id"]
        """See :class:`.SimpleReprMixin`."""

    __tablename__ = "oauth2_server_token"

    __mapper_args__ = {"confirm_deleted_rows": False}

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the server token, auto incremented."""

    client_id = db.Column(
        db.Text, db.ForeignKey("oauth2_server_client.client_id"), nullable=False
    )
    """The client ID of the :class:`.OAuth2ServerClient` the server token belongs to."""

    access_token = db.Column(db.Text, index=True, nullable=False)
    """The actual access token value.

    Note that only a hash of the actual access token value is stored.
    """

    refresh_token = db.Column(db.Text, index=True, nullable=False)
    """The actual refresh token value.

    Note that only a hash of the actual refresh token value is stored.
    """

    client = db.relationship(
        "OAuth2ServerClient", back_populates="oauth2_server_tokens"
    )

    @property
    def is_expired(self):
        """Check if the access token is expired."""

        # We simply delegate to the mixin but use a property to stay consistent with the
        # "AccessTokenMixin".
        return OAuth2TokenMixin.is_expired(self)

    def get_client(self):
        """Get the client for which the token was issued."""
        return self.client

    def get_user(self):
        """Get user the token belongs to."""
        return self.user

    @staticmethod
    def new_access_token(include_prefix=True):
        """Create a new random access token value.

        :param include_prefix: (optional) Whether to include a prefix before the actual
            access token value to distinguish it with other types of access tokens.
        :return: The generated access token value.
        """
        from .utils import new_oauth2_access_token

        return new_oauth2_access_token(include_prefix=include_prefix)

    @staticmethod
    def new_refresh_token():
        """Create a new random refresh token value.

        :return: The generated refresh token value.
        """
        from .utils import new_oauth2_refresh_token

        return new_oauth2_refresh_token()

    @staticmethod
    def hash_token(token):
        """Create a secure hash of an access or refresh token value.

        :param token: The token value to hash.
        :return: The calculated hash as a hexadecimal value.
        """
        prefix = const.ACCESS_TOKEN_PREFIX_OAUTH

        # Exclude the prefix before hashing the token, if applicable.
        if token.startswith(prefix):
            token = token[len(prefix) :]

        return hash_value(token)

    @classmethod
    def get_by_access_token(cls, token):
        """Get a server token using an access token value.

        :param token: The access token value to search for.
        :return: The server token or ``None``.
        """
        token_hash = cls.hash_token(token)
        return cls.query.filter_by(access_token=token_hash).first()

    @classmethod
    def get_by_refresh_token(cls, token):
        """Get a server token using a refresh token value.

        :param token: The refresh token value to search for.
        :return: The server token or ``None``.
        """
        token_hash = cls.hash_token(token)
        return cls.query.filter_by(refresh_token=token_hash).first()

    @classmethod
    def create(
        cls,
        *,
        user,
        client,
        expires_in,
        access_token=None,
        refresh_token=None,
        scope="",
    ):
        """Create a new OAuth2 server token and add it to the database session.

        :param user: The user the server token should belong to.
        :param client: The client the server token should belong to.
        :param expires_in: The expiration time of the access token in seconds.
        :param access_token: (optional) The actual access token value, which will be
            hashed before persisting. Defaults to an access token value created by
            :meth:`new_access_token`.
        :param refresh_token: (optional) The actual refresh token value, which will be
            hashed before persisting. Defaults to a refresh token value created by
            :meth:`new_refresh_token`.
        :param scope: (optional) The scope of the server token.
        :return: The new :class:`.OAuth2ServerToken` object.
        """
        access_token = (
            access_token if access_token is not None else cls.new_access_token()
        )
        refresh_token = (
            refresh_token if refresh_token is not None else cls.new_refresh_token()
        )

        oauth2_server_token = cls(
            user=user,
            client=client,
            expires_in=expires_in,
            access_token=cls.hash_token(access_token),
            refresh_token=cls.hash_token(refresh_token),
            scope=scope,
            token_type=const.OAUTH_TOKEN_TYPE,
        )
        db.session.add(oauth2_server_token)

        return oauth2_server_token


class OAuth2ServerAuthCode(SimpleReprMixin, OAuth2AuthorizationCodeMixin, db.Model):
    """Model to represent OAuth2 authorization codes.

    Required for the implementation of the OAuth2 authorization code grant.
    """

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "client_id"]
        """See :class:`.SimpleReprMixin`."""

    __tablename__ = "oauth2_server_auth_code"

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the authorization code, auto incremented."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` the authorization code belongs to."""

    client_id = db.Column(
        db.Text, db.ForeignKey("oauth2_server_client.client_id"), nullable=False
    )
    """The client ID of the :class:`.OAuth2ServerClient` the auth. code belongs to."""

    scope = db.Column(db.Text, nullable=False, default="")
    """The scope of the authorization code.

    Represented as a single string defining a list of space-delimited scope values.
    """

    user = db.relationship("User", back_populates="oauth2_server_auth_codes")

    client = db.relationship(
        "OAuth2ServerClient", back_populates="oauth2_server_auth_codes"
    )

    @classmethod
    def create(
        cls,
        *,
        user,
        client,
        code,
        redirect_uri,
        scope="",
        code_challenge=None,
        code_challenge_method=None,
        nonce=None,
    ):
        """Create a new OAuth2 authorization code and add it to the database session.

        :param user: The user the authorization code should belong to.
        :param client: The client the authorization code should belong to.
        :param code: The actual authorization code value.
        :param redirect_uri: The allowed redirect URI of the authorization code.
        :param scope: (optional) The scope of the authorization code.
        :param code_challenge: (optional) The code challenge of the authorization code
            used for PKCE.
        :param code_challenge_method: (optional) The code challenge method of the
            authorization code used for PKCE.
        :param nonce: (optional) The nonce of the authorization code.
        :return: The new :class:`.OAuth2ServerAuthCode` object.
        """
        oauth2_auth_code = cls(
            user=user,
            client=client,
            code=code,
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            response_type=const.OAUTH_RESPONSE_TYPE,
            nonce=nonce,
        )
        db.session.add(oauth2_auth_code)

        return oauth2_auth_code

    def is_expired(self):
        """Check if the authorization code is expired.

        :return: ``True`` if the authorization code is expired, ``False`` otherwise.
        """
        expiration_time = self.auth_time + const.OAUTH_AUTH_CODE_EXPIRES_IN
        return expiration_time < int(time())
