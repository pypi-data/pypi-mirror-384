# Copyright 2025 Karlsruhe Institute of Technology
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

from .constants import PLUGIN_NAME


def validate_plugin_config(plugin_config):
    """Validate the given plugin configuration."""
    if not plugin_config.get("endpoint_url") or not plugin_config.get("bucket_name"):
        current_app.logger.error(
            f"Endpoint URL and/or bucket name has not been set for '{PLUGIN_NAME}'"
            " plugin."
        )
        return False

    return True
