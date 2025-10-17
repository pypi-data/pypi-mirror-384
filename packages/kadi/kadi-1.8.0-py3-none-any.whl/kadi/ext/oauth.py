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
from authlib.integrations.flask_client import OAuth
from authlib.integrations.flask_oauth2 import (
    AuthorizationServer as _AuthorizationServer,
)
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc7636 import CodeChallenge

import kadi.lib.constants as const
from kadi.ext.oidc import BearerTokenValidator
from kadi.ext.oidc import OpenIDCode
from kadi.ext.oidc import UserInfoEndpoint
from kadi.lib.oauth.core import AuthorizationCodeGrant
from kadi.lib.oauth.core import RefreshTokenGrant
from kadi.lib.oauth.core import RevocationEndpoint
from kadi.lib.oauth.models import OAuth2ServerClient
from kadi.lib.oauth.models import OAuth2ServerToken
from kadi.lib.oidc.core import normalize_oidc_scopes

from .db import db


class AuthorizationServer(_AuthorizationServer):
    """OAuth2 authorization server for use in a Flask application."""

    def query_client(self, client_id):
        """Retrieve a registered OAuth2 client."""
        client = OAuth2ServerClient.query.filter_by(client_id=client_id).first()

        # Scopes are stored in Kadi notation (with an oidc prefix e.g. oidc.openid).
        # The prefix must be removed to comply with the OIDC standard.
        client.client_metadata["scope"] = normalize_oidc_scopes(
            client.client_metadata["scope"]
        )

        return client

    def save_token(self, token, request):
        """Save an OAuth2 server token in the database."""
        token_data = token

        # Ensure that all required attributes are contained in the token data.
        for attr in ["access_token", "refresh_token", "expires_in"]:
            if attr not in token_data:
                return

        user = request.user
        oauth2_server_client = request.client

        # Make sure that the user only has one token for this client.
        oauth2_server_tokens = user.oauth2_server_tokens.filter(
            OAuth2ServerToken.client_id == oauth2_server_client.client_id
        )
        for oauth2_server_token in oauth2_server_tokens:
            db.session.delete(oauth2_server_token)

        # Make sure we use the correct scope, depending on the grant type. The requested
        # scope is currently always ignored.
        if request.payload.grant_type == const.OAUTH_GRANT_AUTH_CODE:
            # Use the scope of the authorization code, which in turn uses the scope of
            # the client at creation time of the authorization code.
            scope = request.authorization_code.scope
        elif request.payload.grant_type == const.OAUTH_GRANT_REFRESH_TOKEN:
            # Use the scope of the client. If the scope of the client changed, the
            # refresh token grant implementation ensures that the refresh token won't
            # authenticate in the first place.
            scope = oauth2_server_client.scope
        else:
            return

        OAuth2ServerToken.create(
            user=user,
            client=oauth2_server_client,
            scope=scope,
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_in=token_data["expires_in"],
        )
        db.session.commit()


# Extension instance for the OAuth2 server and corresponding grants.
oauth_server = AuthorizationServer()

oauth_server.register_grant(
    AuthorizationCodeGrant, extensions=[CodeChallenge(), OpenIDCode()]
)
oauth_server.register_grant(RefreshTokenGrant)
oauth_server.register_endpoint(RevocationEndpoint)

resource_protector = ResourceProtector()
resource_protector.register_token_validator(BearerTokenValidator())
oauth_server.register_endpoint(UserInfoEndpoint(resource_protector=resource_protector))

# Extension instance for registering OAuth2 providers via plugins.
oauth_registry = OAuth()

# Extension instance for registering OIDC providers for use within the corresponding
# authentication provider.
oidc_registry = OAuth()
