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
from datetime import timedelta

from flask import abort
from flask import current_app
from flask import redirect
from flask import request
from flask import session
from flask_babel import gettext as _
from flask_login import LoginManager
from flask_login import make_next_param

import kadi.lib.constants as const
from kadi.ext.csrf import csrf
from kadi.ext.db import db
from kadi.lib.api.core import get_access_token
from kadi.lib.api.core import json_error_response
from kadi.lib.api.utils import is_api_request
from kadi.lib.security import hash_value
from kadi.lib.utils import utcnow
from kadi.lib.web import flash_info
from kadi.lib.web import url_for
from kadi.modules.accounts.models import User


def _create_session_identifier():
    # We use "remote_addr" directly instead of relying on "X-Forwarded-For" headers. If
    # any proxies sit in front of the application, the ProxyFix middleware provided by
    # Werkzeug should be used to handle that instead.
    return hash_value(f"{request.remote_addr}|{request.user_agent}")


class KadiLoginManager(LoginManager):
    """Custom login manager extension."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._session_identifier_generator = _create_session_identifier

    def _update_remember_cookie(self, response):
        # Completely ignore handling of the "remember_me" cookie since we currently do
        # not use it.
        return response


login = KadiLoginManager()


@login.user_loader
def _load_user_from_session(user_id):
    # Also use CSRF protection (if enabled) when using the API through the session, as
    # the API blueprint is otherwise exempt from it.
    if is_api_request() and current_app.config["WTF_CSRF_ENABLED"]:
        csrf.protect()

    return User.query.get(int(user_id))


@login.request_loader
def _load_user_from_request(request):
    access_token = get_access_token()

    if access_token is not None:
        # Restrict token access to API endpoints only.
        if not is_api_request():
            abort(json_error_response(404))

        if access_token.is_expired:
            abort(json_error_response(401, description="Access token has expired."))

        # Update the last usage date, if applicable.
        if hasattr(access_token, "last_used") and (
            access_token.last_used is None
            or access_token.last_used
            < utcnow() - timedelta(seconds=const.ACCESS_TOKEN_LAST_USED_INTERVAL)
        ):
            access_token.last_used = utcnow()
            db.session.commit()

        return access_token.user

    return None


@login.unauthorized_handler
def _unauthorized():
    if is_api_request():
        return json_error_response(
            401, description="No valid access token was supplied."
        )

    # Store the redirect URL in the session.
    login_url = url_for("accounts.login")
    session[const.SESSION_KEY_NEXT_URL] = make_next_param(login_url, request.url)

    flash_info(_("You have to be logged in to access this page."))
    return redirect(login_url)
