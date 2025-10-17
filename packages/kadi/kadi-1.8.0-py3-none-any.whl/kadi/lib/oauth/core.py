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
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from authlib.oauth2.rfc6749.grants import (
    AuthorizationCodeGrant as _AuthorizationCodeGrant,
)
from authlib.oauth2.rfc6749.grants import RefreshTokenGrant as _RefreshTokenGrant
from authlib.oauth2.rfc7009 import RevocationEndpoint as _RevocationEndpoint
from flask_login import current_user
from sqlalchemy.orm.exc import ObjectDeletedError

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import NestedTransaction
from kadi.lib.db import update_object
from kadi.lib.utils import utcnow

from .models import OAuth2ClientToken
from .models import OAuth2ServerAuthCode
from .models import OAuth2ServerToken


class AuthorizationCodeGrant(_AuthorizationCodeGrant):
    """OAuth2 authorization code grant."""

    TOKEN_ENDPOINT_AUTH_METHODS = [const.OAUTH_TOKEN_ENDPOINT_AUTH_METHOD]
    """Allowed authentication methods for the token endpoint."""

    def save_authorization_code(self, code, request):
        """Save an OAuth2 authorization code in the database."""
        oauth2_server_client = request.client

        # We currently always use the scope that was defined during client registration.
        scope = oauth2_server_client.scope

        # Optional parameters used for PKCE.
        code_challenge = request.payload.data.get("code_challenge")
        code_challenge_method = request.payload.data.get("code_challenge_method")

        oauth2_auth_code = OAuth2ServerAuthCode.create(
            user=request.user,
            client=oauth2_server_client,
            code=code,
            redirect_uri=request.payload.redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            nonce=request.payload.data.get("nonce"),
        )
        db.session.commit()

        return oauth2_auth_code

    def query_authorization_code(self, code, client):
        """Retrieve an existing OAuth2 authorization code."""
        oauth2_auth_code = client.oauth2_server_auth_codes.filter_by(code=code).first()

        if oauth2_auth_code is None or oauth2_auth_code.is_expired():
            return None

        return oauth2_auth_code

    def delete_authorization_code(self, authorization_code):
        """Delete an existing OAuth2 authorization code."""
        with NestedTransaction(exc=ObjectDeletedError) as t:
            db.session.delete(authorization_code)

        if t.success:
            db.session.commit()

    def authenticate_user(self, authorization_code):
        """Authenticate a user related to an OAuth2 authorization code."""
        return authorization_code.user


class RefreshTokenGrant(_RefreshTokenGrant):
    """OAuth2 refresh token grant."""

    TOKEN_ENDPOINT_AUTH_METHODS = [const.OAUTH_TOKEN_ENDPOINT_AUTH_METHOD]
    """Allowed authentication methods for the token endpoint."""

    # Always issue a new refresh token in the token response.
    INCLUDE_NEW_REFRESH_TOKEN = True

    def authenticate_refresh_token(self, refresh_token):
        """Retrieve an existing OAuth2 server token based on a refresh token."""
        oauth2_server_token = OAuth2ServerToken.get_by_refresh_token(refresh_token)

        # If the scope of the retrieved server token does not match the scope of the
        # client anymore, we simply remove it, so the OAuth flow has to be restarted. In
        # the future, we could consider allowing narrower scope.
        if (
            oauth2_server_token is not None
            and oauth2_server_token.scope != oauth2_server_token.client.scope
        ):
            db.session.delete(oauth2_server_token)
            db.session.commit()

            return None

        return oauth2_server_token

    def revoke_old_credential(self, refresh_token):
        """Revoke an old OAuth2 server token."""

        # There is no need to do anything here, as currently old server tokens will be
        # removed anyways by the authorization server implementation whenever a new one
        # is issued.

    def authenticate_user(self, refresh_token):
        """Authenticate a user related to an OAuth2 server token."""
        return refresh_token.user


class RevocationEndpoint(_RevocationEndpoint):
    """OAuth2 token revocation endpoint."""

    CLIENT_AUTH_METHODS = [const.OAUTH_TOKEN_ENDPOINT_AUTH_METHOD]
    """Allowed authentication methods for the revocation endpoint."""

    def query_token(self, token_string, token_type_hint):
        """Retrieve an existing OAuth2 server token."""

        # If a token hint was provided, directly return the result. Note that the
        # returned token will automatically be checked for the correct client ID after
        # returning, so there is no need to do it here.
        if token_type_hint == "access_token":
            return OAuth2ServerToken.get_by_access_token(token_string)

        if token_type_hint == "refresh_token":
            return OAuth2ServerToken.get_by_refresh_token(token_string)

        # Otherwise, check if there is a prefix and fall back to simply checking both
        # token types, starting with the refresh token.
        if token_string.startswith(const.ACCESS_TOKEN_PREFIX_OAUTH):
            return OAuth2ServerToken.get_by_access_token(token_string)

        oauth2_server_token = OAuth2ServerToken.get_by_refresh_token(token_string)

        if oauth2_server_token is None:
            return OAuth2ServerToken.get_by_access_token(token_string)

        return oauth2_server_token

    def revoke_token(self, token, request):
        """Revoke an existing OAuth2 server token."""

        # We simply delete the token here, since even if revoking it, it would be
        # deleted anyways once another token is issued.
        with NestedTransaction(exc=ObjectDeletedError) as t:
            db.session.delete(token)

        if t.success:
            db.session.commit()


def _expiration_to_datetime(expires_at=None, expires_in=None):
    expires_at_datetime = None

    if expires_at is not None:
        expires_at_datetime = datetime.utcfromtimestamp(expires_at).replace(
            tzinfo=timezone.utc
        )
    elif expires_in is not None:
        expires_at_datetime = utcnow() + timedelta(seconds=expires_in)

    return expires_at_datetime


def create_oauth2_client_token(
    *,
    name,
    access_token,
    refresh_token=None,
    user=None,
    expires_at=None,
    expires_in=None,
):
    """Create a new OAuth2 client token.

    :param name: See :attr:`.OAuth2ClientToken.name`.
    :param access_token: See :attr:`.OAuth2ClientToken.access_token`.
    :param refresh_token: (optional) See :attr:`.OAuth2ClientToken.refresh_token`.
    :param user: (optional) The user the client token should belong to. Defaults to the
        current user.
    :param expires_at: (optional) The expiration date and time of the access token as a
        Unix timestamp. Will be prioritized if ``expires_in`` is also given.
    :param expires_in: (optional) The lifetime of the access token in seconds.
    :return: The created OAuth2 client token.
    """
    user = user if user is not None else current_user

    expires_at_datetime = _expiration_to_datetime(
        expires_at=expires_at, expires_in=expires_in
    )

    return OAuth2ClientToken.create(
        user=user,
        name=name,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at_datetime,
    )


def update_oauth2_client_token(
    oauth2_client_token, expires_at=None, expires_in=None, **kwargs
):
    r"""Update an existing OAuth2 client token.

    :param oauth2_client_token: The client token to update.
    :param expires_at: (optional) See :func:`create_oauth2_client_token`.
    :param expires_in: (optional) See :func:`create_oauth2_client_token`.
    :param \**kwargs: Keyword arguments that will be passed to
        :func:`kadi.lib.db.update_object`. See also :func:`create_oauth2_client_token`.
    """
    if expires_at is not None or expires_in is not None:
        kwargs["expires_at"] = _expiration_to_datetime(
            expires_at=expires_at, expires_in=expires_in
        )

    update_object(oauth2_client_token, **kwargs)
