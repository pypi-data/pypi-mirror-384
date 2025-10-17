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
from flask_login import current_user

import kadi.lib.constants as const
from kadi.lib.exceptions import KadiPermissionError
from kadi.lib.permissions.core import add_role
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.core import remove_role
from kadi.modules.accounts.models import User
from kadi.modules.groups.models import Group

from .utils import add_link


def add_links(model, relationship, resource_ids, user=None):
    """Convenience function to link multiple resources together.

    For ease of use in view functions. Uses :func:`kadi.lib.resources.utils.add_link`
    but silently ignores any errors.

    :param model: The model of which the resources to append are instances of. One of
        :class:`.Record` or :class:`.Collection`.
    :param relationship: See :func:`kadi.lib.resources.utils.add_link`.
    :param resource_ids: A list of resource IDs that should be linked referring to
        instances of the given model.
    :param user: (optional) See :func:`kadi.lib.resources.utils.add_link`.
    """
    user = user if user is not None else current_user

    resources_query = model.query.filter(
        model.id.in_(resource_ids), model.state == const.MODEL_STATE_ACTIVE
    )

    for resource in resources_query:
        try:
            add_link(relationship, resource, user=user)
        except KadiPermissionError:
            pass


def update_roles(resource, role_data, user=None):
    """Convenience function to update roles of users and groups.

    For ease of use in view functions. Uses
    :func:`kadi.lib.permissions.core.remove_role` and
    :func:`kadi.lib.permissions.core.add_role`, but silently ignores any errors.

    :param resource: The resource the roles refer to, an instance of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param role_data: A list of dictionaries containing role data corresponding to the
        structure of :class:`.ResourceRoleDataSchema`.
    :param user: (optional) The user performing the operation. Defaults to the current
        user.
    """
    user = user if user is not None else current_user

    for role_meta in role_data:
        subject = None

        if role_meta["subject_type"] == "user":
            subject = User.query.get_active(role_meta["subject_id"])

        # Groups can currently not have roles in other groups.
        elif not isinstance(resource, Group):
            group = Group.query.get_active(role_meta["subject_id"])

            # Only groups readable by the given user can be granted roles.
            if group is not None and has_permission(user, "read", "group", group.id):
                subject = group

        if subject is not None:
            # Do nothing if the subject is the creator of the resource.
            if subject == resource.creator:
                continue

            try:
                # Always remove any roles first. This also allows easily changing
                # existing roles, if applicable.
                remove_role(subject, resource.__tablename__, resource.id)

                if role_meta["role"] is not None:
                    add_role(
                        subject, resource.__tablename__, resource.id, role_meta["role"]
                    )
            except ValueError:
                pass
