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

from kadi.lib.conversion import strip_markdown
from kadi.lib.resources.core import create_resource
from kadi.lib.resources.core import delete_resource
from kadi.lib.resources.core import purge_resource
from kadi.lib.resources.core import restore_resource
from kadi.lib.resources.core import update_resource

from .models import Group
from .models import GroupState
from .models import GroupVisibility


def create_group(
    *,
    identifier,
    title,
    creator=None,
    description="",
    visibility=GroupVisibility.PRIVATE,
    state=GroupState.ACTIVE,
):
    """Create a new group.

    Uses :func:`kadi.lib.resources.core.create_resource`.

    :param identifier: See :attr:`.Group.identifier`.
    :param title: See :attr:`.Group.title`.
    :param creator: (optional) The creator of the group. Defaults to the current user.
    :param description: (optional) See :attr:`.Group.description`.
    :param visibility: (optional) See :attr:`.Group.visibility`.
    :param state: (optional) See :attr:`.Group.state`.
    :return: See :func:`kadi.lib.resources.core.create_resource`.
    """
    creator = creator if creator is not None else current_user

    return create_resource(
        Group,
        creator=creator,
        identifier=identifier,
        title=title,
        description=description,
        plain_description=strip_markdown(description),
        visibility=visibility,
        state=state,
    )


def update_group(group, user=None, **kwargs):
    r"""Update an existing group.

    Uses :func:`kadi.lib.resources.core.update_resource`.

    :param group: The group to update.
    :param user: (optional) The user who triggered the update. Defaults to the current
        user.
    :param \**kwargs: Keyword arguments that will be passed to
        :func:`kadi.lib.resources.update_resource`. See also :func:`create_group`.
    :return: See :func:`kadi.lib.resources.core.update_resource`.
    """
    user = user if user is not None else current_user

    if "description" in kwargs:
        kwargs["plain_description"] = strip_markdown(kwargs["description"])

    return update_resource(group, user=user, **kwargs)


def delete_group(group, user=None):
    """Delete an existing group.

    Uses :func:`kadi.lib.resources.core.delete_resource`.

    :param group: The group to delete.
    :param user: (optional) The user who triggered the deletion. Defaults to the current
        user.
    """
    user = user if user is not None else current_user
    delete_resource(group, user=user)


def restore_group(group, user=None):
    """Restore a deleted group.

    Uses :func:`kadi.lib.resources.core.restore_resource`.

    :param group: The group to restore.
    :param user: (optional) The user who triggered the restoration. Defaults to the
        current user.
    """
    user = user if user is not None else current_user
    restore_resource(group, user=user)


def purge_group(group):
    """Purge an existing group.

    Uses :func:`kadi.lib.resources.core.purge_resource`.

    :param group: The group to purge.
    """
    from .utils import delete_group_image

    delete_group_image(group)
    purge_resource(group)
