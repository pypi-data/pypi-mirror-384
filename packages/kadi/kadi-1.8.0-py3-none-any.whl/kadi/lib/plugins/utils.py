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
from flask import current_app
from flask import json

import kadi.lib.constants as const
from kadi.lib.utils import flatten_list

from .core import run_hook


def get_plugin_scripts():
    """Convenience function to retrieve all script URLs provided by plugins.

    Uses the :func:`kadi.plugins.spec.kadi_get_scripts` plugin hook to collect the
    script URLs.

    :return: A flattened list of all script URLs or an empty list if something went
        wrong while collecting the scripts.
    """
    try:
        urls = flatten_list(run_hook("kadi_get_scripts"))
    except Exception as e:
        current_app.logger.exception(e)
        return []

    return urls


def get_plugin_frontend_translations():
    """Convenience function to collect all frontend translations provided by plugins.

    Uses the :func:`kadi_get_translations_bundles` plugin hook to collect and merge the
    translation bundles.

    :return: A dictionary mapping each possible locale of the application to the merged
        translation bundles.
    """
    translations = {}

    for locale in const.LOCALES:
        translations[locale] = {}

        try:
            bundles = run_hook("kadi_get_translations_bundles", locale=locale)

            for bundle in bundles:
                if not isinstance(bundle, dict):
                    current_app.logger.error("Invalid translations bundle format.")
                    continue

                translations[locale].update(bundle)

        except Exception as e:
            current_app.logger.exception(e)

    return translations


def get_plugin_terms(query, page, per_page):
    """Convenience function to collect terms provided by a plugin.

    Uses the :func:`kadi_get_terms` plugin hook to collect the terms.

    :param query: The search query.
    :param page: The current result page used for pagination.
    :param per_page: The number of results per page used for pagination.
    :return: A tuple containing the total number of terms and a list of the terms
        themselves.
    """
    default_result = (0, [])
    error_msg = "Invalid terms format."

    try:
        result = run_hook("kadi_get_terms", query=query, page=page, per_page=per_page)
    except Exception as e:
        current_app.logger.exception(e)
        return default_result

    if not isinstance(result, tuple) or len(result) != 2:
        current_app.logger.error(error_msg)
        return default_result

    total, items = result

    # pylint: disable=unidiomatic-typecheck
    if type(total) is not int or not isinstance(items, list):
        current_app.logger.error(error_msg)
        return default_result

    for item in items:
        if not isinstance(item, dict) or "term" not in item:
            current_app.logger.error(error_msg)
            return default_result

        if "body" not in item:
            item["body"] = item["term"]

    try:
        # Check whether the contents are JSON serializable.
        json.dumps(items, sort_keys=False)
    except Exception as e:
        current_app.logger.exception(e)
        return default_result

    return total, items
