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
import os

from flask import Blueprint

import kadi.lib.constants as const
from kadi.ext.csrf import csrf
from kadi.lib.utils import as_list


class APIBlueprint(Blueprint):
    """Custom Flask blueprint with support for API versioning."""

    def route(self, rule, **options):
        r"""Decorator to register a view function for a given URL rule.

        Adds a new option ``v`` to Flask's ``route`` decorator to support API versioning
        within endpoints.

        **Example:**

        .. code-block:: python3

            @blueprint.route("/records", v=["v1", "v2"])
            def get_records():
                pass

        Each specified API version has to be valid, otherwise it will be ignored. If no
        versions are given, the endpoint defaults to all available versions. The regular
        endpoint without any version will be created as well, pointing to the same
        function as the endpoint corresponding to the version defined in
        :const:`kadi.lib.constants.API_VERSION_DEFAULT`.

        The code snippet above would lead to the following endpoints and URLs, assuming
        one of the given versions corresponds to the default API version:

        * ``api.get_records``    -> ``/api/records``
        * ``api.get_records_v1`` -> ``/api/v1/records``
        * ``api.get_records_v2`` -> ``/api/v2/records``

        :param rule: The URL rule as string.
        :param endpoint: (optional) The endpoint for the registered URL rule. Defaults
            to the name of the function.
        :param v: (optional) A string or list of strings specifying the supported API
            versions.
        :param \**options: Additional options to be forwarded to the underlying rule
            system of Flask.
        """

        def decorator(func):
            endpoint = options.pop("endpoint", func.__name__)
            versions = as_list(options.pop("v", const.API_VERSIONS))

            for version in versions:
                if version not in const.API_VERSIONS:
                    continue

                self.add_url_rule(
                    f"{version}{rule}", f"{endpoint}_{version}", func, **options
                )

                if version == const.API_VERSION_DEFAULT:
                    self.add_url_rule(rule, endpoint, func, **options)

            return func

        return decorator

    def _check_setup_finished(self, *args):
        # This environment variable check can be used as a workaround to disable the
        # checks regarding the route setup order of this blueprint in certain cases.
        if os.environ.get(const.VAR_API_BP) != "1":
            super()._check_setup_finished(*args)


bp = APIBlueprint("api", __name__, url_prefix="/api")

# The API blueprint is exempt from CSRF (except when using the API through the session,
# see the user loader in "lib/ext/login.py").
csrf.exempt(bp)


# pylint: disable=unused-import


import kadi.modules.accounts.api  # noqa
import kadi.modules.collections.api  # noqa
import kadi.modules.groups.api  # noqa
import kadi.modules.main.api  # noqa
import kadi.modules.records.api  # noqa
import kadi.modules.settings.api  # noqa
import kadi.modules.sysadmin.api  # noqa
import kadi.modules.templates.api  # noqa
