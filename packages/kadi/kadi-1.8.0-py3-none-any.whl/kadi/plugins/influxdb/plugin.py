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


# pylint: disable=missing-function-docstring


from flask import render_template
from flask import request

from kadi.lib.config.core import get_user_config
from kadi.lib.plugins.core import PluginBlueprint
from kadi.lib.plugins.core import get_plugin_config
from kadi.lib.utils import as_list
from kadi.lib.web import url_for
from kadi.plugins import hookimpl

from .constants import PLUGIN_NAME
from .constants import USER_CONFIG_INFLUXDBS
from .core import InfluxDBConfigForm
from .utils import check_group_access
from .utils import get_user_group_ids
from .utils import validate_instance_config


@hookimpl
def kadi_get_blueprints():
    return PluginBlueprint(
        PLUGIN_NAME,
        __name__,
        url_prefix=f"/{PLUGIN_NAME}",
        template_folder="templates",
        static_folder="static",
    )


@hookimpl
def kadi_get_scripts():
    if request.endpoint != "settings.manage_preferences":
        return None

    return url_for(f"{PLUGIN_NAME}.static", filename="influxdb-field.js")


TRANSLATIONS = {
    "de": {
        "Configured globally": "Global konfiguriert",
        "Database disabled or no access rights.": "Datenbank deaktiviert oder keine"
        " Zugriffsrechte.",
        "Name": "Name",
        "Query endpoint:": "Query-Endpunkt:",
        "Token": "Token",
    }
}


@hookimpl
def kadi_get_translations_bundles(locale):
    if request.endpoint != "settings.manage_preferences":
        return None

    return TRANSLATIONS.get(locale)


@hookimpl
def kadi_get_preferences_config():
    plugin_config = get_plugin_config(PLUGIN_NAME)
    user_groups = get_user_group_ids()
    influxdbs = {}

    for name in plugin_config:
        group_ids = as_list(plugin_config[name].get("groups"))

        if validate_instance_config(plugin_config, name) and check_group_access(
            user_groups, group_ids
        ):
            influxdbs[name] = {
                "title": plugin_config[name].get("title", name),
                "has_token": bool(plugin_config[name].get("token")),
                "query_endpoint": url_for("api.influxdb_query", name=name, orgID="..."),
            }

    user_config = get_user_config(key=USER_CONFIG_INFLUXDBS, decrypt=True)

    # Check if either at least one valid InfluxDB instance is configured or if the
    # current user has configured any InfluxDB instance in the past.
    if not influxdbs and not user_config:
        return None

    form = InfluxDBConfigForm()

    return {
        "title": "InfluxDB",
        "form": form,
        "get_template": lambda: render_template(
            "influxdb/preferences.html", form=form, influxdbs=influxdbs
        ),
    }
