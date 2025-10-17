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

from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import internal
from kadi.lib.api.core import json_response
from kadi.lib.api.models import PersonalToken
from kadi.lib.api.schemas import PersonalTokenSchema
from kadi.lib.api.utils import create_pagination_data
from kadi.lib.oauth.models import OAuth2ServerClient
from kadi.lib.oauth.models import OAuth2ServerToken
from kadi.lib.oauth.schemas import OAuth2ServerClientSchema
from kadi.lib.oauth.schemas import OAuth2ServerTokenSchema
from kadi.lib.web import paginated


@bp.get("/settings/personal-tokens")
@login_required
@internal
@paginated
def get_personal_tokens(page, per_page):
    """Get personal tokens of the current user."""
    paginated_tokens = current_user.personal_tokens.order_by(
        PersonalToken.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    data = {
        "items": PersonalTokenSchema(many=True).dump(paginated_tokens),
        **create_pagination_data(paginated_tokens.total, page, per_page),
    }
    return json_response(200, data)


@bp.get("/settings/applications/registered")
@login_required
@internal
@paginated
def get_registered_applications(page, per_page):
    """Get registered OAuth2 applications of the current user."""
    paginated_applications = current_user.oauth2_server_clients.order_by(
        OAuth2ServerClient.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    data = {
        "items": OAuth2ServerClientSchema(many=True).dump(paginated_applications),
        **create_pagination_data(paginated_applications.total, page, per_page),
    }
    return json_response(200, data)


@bp.get("/settings/applications/authorized")
@login_required
@internal
@paginated
def get_authorized_applications(page, per_page):
    """Get authorized OAuth2 applications of the current user."""
    paginated_applications = (
        current_user.oauth2_server_tokens.join(OAuth2ServerClient)
        .with_entities(
            OAuth2ServerToken.id,
            OAuth2ServerToken.scope,
            OAuth2ServerClient._client_metadata.label("client"),
        )
        .order_by(OAuth2ServerToken.id.desc())
    ).paginate(page=page, per_page=per_page, error_out=False)

    data = {
        "items": OAuth2ServerTokenSchema(many=True).dump(paginated_applications),
        **create_pagination_data(paginated_applications.total, page, per_page),
    }
    return json_response(200, data)
