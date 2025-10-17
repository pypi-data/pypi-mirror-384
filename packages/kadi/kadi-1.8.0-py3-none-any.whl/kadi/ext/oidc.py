# Copyright 2025 Karlsruhe Institute of Technology
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
from authlib.oauth2 import OAuth2Error
from authlib.oauth2.rfc6750 import BearerTokenValidator as _BearerTokenValidator
from authlib.oauth2.rfc6750 import InsufficientScopeError
from authlib.oauth2.rfc6750 import InvalidTokenError
from authlib.oidc.core import UserInfoEndpoint as _UserInfoEndpoint
from authlib.oidc.core.grants import OpenIDCode as _OpenIDCode
from flask import current_app

from kadi.lib.api.core import get_access_token
from kadi.lib.oidc.core import generate_user_info
from kadi.lib.oidc.core import get_active_signing_key
from kadi.lib.oidc.core import get_issuer
from kadi.lib.oidc.core import is_nonce_used
from kadi.lib.oidc.core import jwk_thumbprint_rsa


def _check_singing_key(key):
    if not key:
        raise OAuth2Error(error="server_error", description="Signing key unavailable.")


class OpenIDCode(_OpenIDCode):
    """Extension to handle OpenID Connect requests for the code grant type."""

    def get_jwt_config(self, grant):
        key = get_active_signing_key()

        _check_singing_key(key)

        return {
            "key": key,
            "alg": "RS256",
            "iss": get_issuer(),
            "exp": current_app.config.get("OIDC_ID_TOKEN_EXPIRES_IN", 3600),
            "kid": jwk_thumbprint_rsa(key.public_key()),
        }

    def exists_nonce(self, nonce, request):
        """Checks if a nonce was already used by a client.

        :returns: True if the nonce was already used, False otherwise.
        """
        return is_nonce_used(request.payload.data.get("client_id"), nonce)

    def generate_user_info(self, user, scope):
        """Generates the user info with the requested OIDC scopes.

        :returns: The OIDC user info used in the ID token.
        """
        return generate_user_info(user, scope)


class BearerTokenValidator(_BearerTokenValidator):
    """Validates a bearer token in a OIDC request."""

    def authenticate_token(self, token_string):
        """Get the token for the request."""
        return get_access_token()

    def validate_token(self, token, scopes, request):
        """Check if token is active and matches the requested scopes."""
        if not token:
            raise InvalidTokenError(
                realm=self.realm, extra_attributes=self.extra_attributes
            )
        if token.is_expired:
            raise InvalidTokenError(
                realm=self.realm, extra_attributes=self.extra_attributes
            )

        if token.is_revoked():
            raise InvalidTokenError(
                realm=self.realm, extra_attributes=self.extra_attributes
            )

        if self.scope_insufficient(token.get_scope(), scopes):
            raise InsufficientScopeError()


class UserInfoEndpoint(_UserInfoEndpoint):
    """Endpoint that provides consented claims about the logged in user."""

    def get_issuer(self):
        """Get the issuer of the ID token."""
        return get_issuer()

    def generate_user_info(self, user, scope):
        """Generates the user info with the requested OIDC scopes.

        :returns: The OIDC user info used in the ID token.
        """
        return generate_user_info(user, scope)

    def resolve_private_key(self):
        """Get the private key for signing ID tokens.

        :returns: The signing key.
        """
        key = get_active_signing_key()

        _check_singing_key(key)

        return key
