# Copyright 2023 Karlsruhe Institute of Technology
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
from marshmallow import fields

import kadi.lib.constants as const
from kadi.lib.schemas import BaseSchema
from kadi.lib.web import url_for


class OAuth2ServerClientSchema(BaseSchema):
    """Schema to represent OAuth2 clients.

    See :class:`.OAuth2ServerClient`.
    """

    id = fields.Integer(dump_only=True)

    client_id = fields.String(dump_only=True)

    client_name = fields.String(dump_only=True)

    client_uri = fields.String(dump_only=True)

    scope = fields.String(dump_only=True)

    created_at = fields.DateTime(dump_only=True)

    _links = fields.Method("_generate_links")

    def _generate_links(self, obj):
        return {
            "edit": url_for("settings.edit_application", id=obj.id),
            "authorize": url_for(
                "main.oauth2_server_authorize",
                response_type=const.OAUTH_RESPONSE_TYPE,
                client_id=obj.client_id,
                redirect_uri=obj.get_default_redirect_uri(),
            ),
        }


class OAuth2ServerTokenSchema(BaseSchema):
    """Schema to represent OAuth2 server tokens.

    See also :class:`.OAuth2ServerToken`.
    """

    id = fields.Integer(dump_only=True)

    scope = fields.String(dump_only=True)

    client = fields.Nested(
        "OAuth2ServerClientSchema", only=["client_name", "client_uri"], dump_only=True
    )

    _actions = fields.Method("_generate_actions")

    def _generate_actions(self, obj):
        return {
            "remove": url_for("api.remove_oauth2_server_token", id=obj.id),
        }
