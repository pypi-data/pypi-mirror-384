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


# pylint: disable=missing-function-docstring


from flask import Blueprint

import kadi.lib.constants as const
from kadi.lib.plugins.core import get_plugin_config
from kadi.plugins import hookimpl

from .constants import DEFAULT_ENDPOINT
from .constants import PLUGIN_NAME
from .core import search_terms


@hookimpl
def kadi_get_blueprints():
    return Blueprint(PLUGIN_NAME, __name__, template_folder="templates")


@hookimpl
def kadi_get_capabilities():
    return const.CAPABILITY_TERM_SEARCH


@hookimpl
def kadi_get_terms(query, page, per_page):
    plugin_config = get_plugin_config(PLUGIN_NAME)
    endpoint = plugin_config.get("endpoint", DEFAULT_ENDPOINT)

    return search_terms(endpoint, query, page, per_page)
