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


# pylint: disable=missing-function-docstring


import os

from flask import render_template
from flask import request
from flask_babel import gettext as _

import kadi.lib.constants as const
from kadi.lib.oauth.utils import get_refresh_token_handler
from kadi.lib.plugins.core import PluginBlueprint
from kadi.lib.plugins.core import get_plugin_config
from kadi.lib.web import url_for
from kadi.modules.records.models import Record
from kadi.plugins import hookimpl

from .constants import DEFAULT_URL
from .constants import PLUGIN_NAME
from .constants import URL_INVENIO_DOCS
from .core import ZenodoForm
from .core import upload_resource
from .utils import validate_plugin_config


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
    endpoints = {
        "records.publish_record",
        "collections.publish_collection",
    }

    if request.endpoint not in endpoints or not request.path.endswith(PLUGIN_NAME):
        return None

    return url_for(f"{PLUGIN_NAME}.static", filename="export-filter-field.js")


@hookimpl
def kadi_get_translations_paths():
    return os.path.join(os.path.dirname(__file__), "translations")


@hookimpl
def kadi_register_oauth2_providers(registry):
    plugin_config = get_plugin_config(PLUGIN_NAME)

    if not validate_plugin_config(plugin_config):
        return

    client_id = plugin_config["client_id"]
    client_secret = plugin_config["client_secret"]
    base_url = plugin_config.get("base_url", DEFAULT_URL)

    registry.register(
        name=PLUGIN_NAME,
        client_id=client_id,
        client_secret=client_secret,
        access_token_url=f"{base_url}/oauth/token",
        access_token_params={"client_id": client_id, "client_secret": client_secret},
        authorize_url=f"{base_url}/oauth/authorize",
        api_base_url=f"{base_url}/api/",
        client_kwargs={"scope": "deposit:write"},
        compliance_fix=get_refresh_token_handler(client_id, client_secret),
    )


@hookimpl
def kadi_get_oauth2_providers():
    plugin_config = get_plugin_config(PLUGIN_NAME)

    if not validate_plugin_config(plugin_config):
        return None

    description = _(
        "Zenodo is a general-purpose open-access repository developed and operated by"
        " CERN. It allows researchers to deposit and publish data sets, research"
        " software, reports, and any other research related digital objects. Connecting"
        " your account to Zenodo makes it possible to directly upload resources to"
        " Zenodo."
    )

    return {
        "name": PLUGIN_NAME,
        "title": "Zenodo",
        "website": plugin_config.get("base_url", DEFAULT_URL),
        "description": description,
    }


@hookimpl
def kadi_get_publication_providers(resource):
    plugin_config = get_plugin_config(PLUGIN_NAME)

    if isinstance(resource, Record):
        export_endpoint = "records.export_record"
    else:
        export_endpoint = "collections.export_collection"

    warning_msg = plugin_config.get("warning_msg")
    export_url = url_for(
        export_endpoint, id=resource.id, export_type=const.EXPORT_TYPE_RO_CRATE
    )

    return {
        "name": PLUGIN_NAME,
        "description": render_template(
            "zenodo/description_publication.html",
            warning_msg=warning_msg,
            export_url=export_url,
            invenio_url=URL_INVENIO_DOCS,
        ),
    }


@hookimpl
def kadi_get_publication_form(provider, resource):
    if provider != PLUGIN_NAME:
        return None

    return ZenodoForm(data={"export_filter": {"user": True}})


@hookimpl
def kadi_get_publication_form_template(provider, resource, form):
    if provider != PLUGIN_NAME:
        return None

    return render_template("zenodo/publication_form.html", form=form, resource=resource)


@hookimpl
def kadi_publish_resource(provider, resource, form_data, user, client, token, task):
    if provider != PLUGIN_NAME:
        return None

    return upload_resource(resource, form_data, user, client, token, task)
