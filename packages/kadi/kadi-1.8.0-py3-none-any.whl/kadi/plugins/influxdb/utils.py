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

from kadi.modules.groups.models import Group
from kadi.modules.groups.utils import get_user_groups

from .constants import PLUGIN_NAME


def validate_instance_config(plugin_config, name):
    """Validate the given InfluxDB instance name of the given plugin configuration."""
    instance_config = plugin_config.get(name)

    if not isinstance(instance_config, dict) or not instance_config.get("url"):
        current_app.logger.error(
            f"Invalid configuration for instance '{name}' in '{PLUGIN_NAME}' plugin."
        )
        return False

    return True


def get_user_group_ids():
    """Get a set of group IDs the current user is a member of."""
    user_groups = get_user_groups().with_entities(Group.id)
    return {group_id for (group_id,) in user_groups}


def check_group_access(user_groups, valid_groups):
    """Check if a set of user group IDs intersects with another set of group IDs."""
    return valid_groups is None or bool(user_groups.intersection(valid_groups))
