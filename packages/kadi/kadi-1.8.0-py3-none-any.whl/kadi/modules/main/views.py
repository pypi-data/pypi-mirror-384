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
from authlib.oauth2 import OAuth2Error
from flask import redirect
from flask import render_template
from flask_babel import gettext as _
from flask_login import current_user
from flask_login import login_required

import kadi.lib.constants as const
from kadi.ext.csrf import csrf
from kadi.ext.oauth import oauth_server
from kadi.lib.api.core import json_response
from kadi.lib.config.core import get_sys_config
from kadi.lib.oauth.core import AuthorizationCodeGrant
from kadi.lib.oauth.core import RevocationEndpoint
from kadi.lib.oidc.core import get_issuer
from kadi.lib.oidc.core import get_jwks
from kadi.lib.openapi import OpenAPISpec
from kadi.lib.web import get_preferred_locale
from kadi.lib.web import html_error_response
from kadi.lib.web import qparam
from kadi.lib.web import url_for

from .blueprint import bp
from .forms import AuthorizeApplicationForm
from .utils import get_favorite_resources
from .utils import get_latest_resources
from .utils import get_resource_searches


@bp.get("/")
def index():
    """The index/home page.

    Will change depending on whether the current user is authenticated or not.
    """
    preferred_locale = get_preferred_locale()

    if not current_user.is_authenticated:
        return render_template("main/index.html", preferred_locale=preferred_locale)

    return render_template(
        "main/home.html",
        title=_("Home"),
        preferred_locale=preferred_locale,
        js_context={
            "favorite_resources": get_favorite_resources(),
            "saved_searches": get_resource_searches(),
            "latest_resources": get_latest_resources(),
        },
    )


@bp.get("/about")
def about():
    """The about page."""
    return render_template("main/about.html", title=_("About"))


@bp.get("/help")
def help():
    """The help page."""
    return render_template("main/help.html", title=_("Help"))


@bp.get("/terms-of-use")
def terms_of_use():
    """Page showing the terms of use, if configured."""
    config_item = const.SYS_CONFIG_TERMS_OF_USE

    if not get_sys_config(config_item):
        return redirect(url_for("main.index"))

    return render_template(
        "main/legals.html",
        title=_("Terms of use"),
        endpoint="terms_of_use",
        config_item=config_item,
    )


@bp.get("/privacy-policy")
def privacy_policy():
    """Page showing the privacy policy, if configured."""
    config_item = const.SYS_CONFIG_PRIVACY_POLICY

    if not get_sys_config(config_item):
        return redirect(url_for("main.index"))

    return render_template(
        "main/legals.html",
        title=_("Privacy policy"),
        endpoint="privacy_policy",
        config_item=config_item,
    )


@bp.get("/legal-notice")
def legal_notice():
    """Page showing the legal notice, if configured."""
    config_item = const.SYS_CONFIG_LEGAL_NOTICE

    if not get_sys_config(config_item):
        return redirect(url_for("main.index"))

    return render_template(
        "main/legals.html",
        title=_("Legal notice"),
        endpoint="legal_notice",
        config_item=config_item,
    )


@bp.get("/openapi.json")
@qparam("v")
@login_required
def apispec(qparams):
    """Endpoint to retrieve an OpenAPI specification of the HTTP API."""
    apispec = OpenAPISpec(qparams["v"])
    return json_response(200, apispec.spec)


@bp.route("/oauth/authorize", methods=["GET", "POST"])
@login_required
def oauth2_server_authorize():
    """Authorization endpoint for the OAuth2 server implementation."""
    form = AuthorizeApplicationForm()

    try:
        grant = oauth_server.get_consent_grant(end_user=current_user)
    except OAuth2Error as e:
        description = e.description

        if not description:
            description = _(
                "The service that redirected you here made an invalid authorization"
                " request."
            )

        return html_error_response(e.status_code, description=description)

    if form.validate_on_submit():
        # Check if authorization was granted by the user.
        if form.submit_auth.data:
            grant_user = current_user
        else:
            grant_user = None

        return oauth_server.create_authorization_response(
            grant_user=grant_user, grant=grant
        )

    return render_template(
        "main/oauth_consent.html",
        title=_("Authorize application"),
        form=form,
        client=grant.client,
    )


@bp.post("/oauth/token")
@csrf.exempt
def oauth2_server_token():
    """Token endpoint for the OAuth2 server implementation."""
    return oauth_server.create_token_response()


@bp.post("/oauth/revoke")
@csrf.exempt
def oauth2_server_revoke():
    """Token revocation endpoint for the OAuth2 server implementation."""
    return oauth_server.create_endpoint_response(RevocationEndpoint.ENDPOINT_NAME)


@bp.get("/oauth/jwks.json")
def openid_jwks():
    """Get the JSON Web Key Set."""
    return json_response(200, get_jwks())


@bp.get("/.well-known/openid-configuration")
def openid_configuration():
    """Discovery endpoint for OpenID connect."""

    data = {
        "issuer": get_issuer(),
        "authorization_endpoint": url_for("main.oauth2_server_authorize"),
        "token_endpoint": url_for("main.oauth2_server_token"),
        "userinfo_endpoint": url_for("api.openid_userinfo"),
        "jwks_uri": url_for("main.openid_jwks"),
        "response_types_supported": list(AuthorizationCodeGrant.RESPONSE_TYPES),
        "scopes_supported": ["openid", "profile", "email"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "token_endpoint_auth_methods_supported": list(
            AuthorizationCodeGrant.TOKEN_ENDPOINT_AUTH_METHODS
        ),
        "claims_supported": [
            "sub",
            "iss",
            "aud",
            "exp",
            "iat",
            "auth_time",
            "name",
            "email",
            "email_verified",
        ],
    }

    return json_response(200, data)
