# Copyright 2024 Karlsruhe Institute of Technology
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
import os

from flask import current_app
from flask import json

from kadi.ext.db import db
from kadi.lib.db import escape_like
from kadi.lib.plugins.core import run_hook

from .models import License


def get_licenses(filter_term=""):
    """Get all licenses stored in the database.

    :param filter_term: (optional) A (case insensitive) term to filter the licenses by
        their title or name.
    :return: The licenses as query, ordered by their title in ascending order.
    """
    filter_term = escape_like(filter_term)
    licenses_query = License.query.filter(
        db.or_(
            License.title.ilike(f"%{filter_term}%"),
            License.name.ilike(f"%{filter_term}%"),
        )
    ).order_by(License.title)

    return licenses_query


def get_builtin_licenses():
    """Get all built-in licenses from their resource file.

    :return: The licenses as dictionary, mapping the unique name of each license to
        another dictionary, containing the title (``"title"``) and url (``"url"``) of
        each license.
    """
    licenses_path = os.path.join(
        current_app.config["RESOURCES_PATH"], "opendefinition.json"
    )

    with open(licenses_path, encoding="utf-8") as f:
        return json.load(f)


def get_plugin_licenses():
    """Get all licenses added via plugins.

    Uses the :func:`kadi.plugins.spec.kadi_get_licenses` plugin hook to collect the
    licenses. Invalid licenses will be ignored.

    :return: The licenses as dictionary, in the same format as returned via
        :func:`get_builtin_licenses`.
    """
    plugin_licenses = {}

    try:
        license_data = run_hook("kadi_get_licenses")
    except Exception as e:
        current_app.logger.exception(e)
        return plugin_licenses

    for licenses in license_data:
        if not isinstance(licenses, dict):
            current_app.logger.error("Invalid license data format.")
            continue

        for name, license_meta in licenses.items():
            if not isinstance(license_meta, dict) or not "title" in license_meta:
                current_app.logger.error(f"Invalid license metadata for '{name}'.")
                continue

            plugin_licenses[name] = {
                "title": license_meta["title"],
                "url": license_meta.get("url"),
            }

    return plugin_licenses
