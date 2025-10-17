# Copyright 2022 Karlsruhe Institute of Technology
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
import requests
from flask import current_app
from flask import request
from flask_login import login_required
from marshmallow import ValidationError
from marshmallow import fields

import kadi.lib.constants as const
from kadi.lib.api.blueprint import bp as api_bp
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.config.core import get_user_config
from kadi.lib.forms import JSONField
from kadi.lib.plugins.core import PluginConfigForm
from kadi.lib.plugins.core import get_plugin_config
from kadi.lib.schemas import BaseSchema
from kadi.lib.utils import as_list
from kadi.lib.web import qparam

from .constants import DEFAULT_CONTENT_TYPE
from .constants import PLUGIN_NAME
from .constants import USER_CONFIG_INFLUXDBS
from .utils import check_group_access
from .utils import get_user_group_ids
from .utils import validate_instance_config


class _InfluxDBSchema(BaseSchema):
    name = fields.String(required=True)

    token = fields.String(required=True)

    title = fields.String(required=True)


class InfluxDBField(JSONField):
    """Custom field to process and validate InfluxDB instances."""

    def __init__(self, *args, **kwargs):
        kwargs["default"] = []
        super().__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)

        if valuelist:
            try:
                schema = _InfluxDBSchema(many=True)
                self.data = schema.load(self.data)

            except ValidationError as e:
                self.data = self.default
                raise ValueError("Invalid data structure.") from e


class InfluxDBConfigForm(PluginConfigForm):
    """Form for configuring InfluxDB instances."""

    influxdbs = InfluxDBField()

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, plugin_name=PLUGIN_NAME, encrypted_fields={"influxdbs"}, **kwargs
        )


@api_bp.post("/influxdb/<name>/query")
@login_required
@qparam("orgID")
def influxdb_query(name, qparams):
    """Query data from a configured InfluxDB instance.

    This endpoint is simply a proxy to the InfluxDB query endpoint documented at:
    https://docs.influxdata.com/influxdb/v2/api/#operation/PostQuery
    """
    plugin_config = get_plugin_config(PLUGIN_NAME)

    if name not in plugin_config:
        return json_error_response(404)

    if not validate_instance_config(plugin_config, name):
        return json_error_response(
            500, description=f"InfluxDB instance '{name}' is configured incorrectly."
        )

    instance_config = plugin_config[name]
    group_ids = as_list(instance_config.get("groups"))

    if not check_group_access(get_user_group_ids(), group_ids):
        return json_error_response(403)

    user_config = get_user_config(key=USER_CONFIG_INFLUXDBS, default=[], decrypt=True)
    user_config = {config["name"]: config for config in user_config}

    # Globally provided token.
    if instance_config.get("token"):
        used_token = instance_config["token"]
    # User provided token.
    elif name in user_config and user_config[name].get("token"):
        used_token = user_config[name]["token"]
    else:
        return json_error_response(
            401, description=f"No access token was supplied for InfluxDB '{name}'."
        )

    # Set the headers required by InfluxDB.
    content_type = request.content_type

    if content_type not in {DEFAULT_CONTENT_TYPE, const.MIMETYPE_JSON}:
        content_type = DEFAULT_CONTENT_TYPE

    headers = {
        "Authorization": f"Token {used_token}",
        "Content-Type": content_type,
    }

    try:
        endpoint = f"{instance_config['url']}/api/v2/query?orgID={qparams['orgID']}"
        response = requests.post(
            endpoint,
            data=request.data,
            headers=headers,
            timeout=instance_config.get("timeout", 10),
        )
    except Exception as e:
        current_app.logger.exception(e)
        return json_error_response(
            502, description=f"Request to InfluxDB '{name}' failed."
        )

    # Return errors that are produced directly by the accessed InfluxDB instance as-is.
    if response.status_code != 200:
        return json_response(response.status_code, response.json())

    return current_app.response_class(
        response=response.content, mimetype=const.MIMETYPE_CSV
    )
