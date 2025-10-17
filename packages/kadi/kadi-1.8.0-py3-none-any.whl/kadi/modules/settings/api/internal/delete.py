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
from flask_login import current_user
from flask_login import login_required

from kadi.ext.db import db
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import internal
from kadi.lib.api.core import json_response
from kadi.lib.api.models import PersonalToken
from kadi.lib.oauth.models import OAuth2ServerToken


@bp.delete("/settings/personal-tokens/<int:id>")
@login_required
@internal
def remove_personal_token(id):
    """Remove a personal token of the current user."""
    personal_token = current_user.personal_tokens.filter(
        PersonalToken.id == id
    ).first_or_404()

    db.session.delete(personal_token)
    db.session.commit()

    return json_response(204)


@bp.delete("/settings/oauth-tokens/<int:id>")
@login_required
@internal
def remove_oauth2_server_token(id):
    """Remove an OAuth2 server token of the current user."""
    oauth2_server_token = current_user.oauth2_server_tokens.filter(
        OAuth2ServerToken.id == id
    ).first_or_404()

    db.session.delete(oauth2_server_token)
    db.session.commit()

    return json_response(204)
