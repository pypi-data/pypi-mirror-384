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

from kadi.ext.db import db
from kadi.lib.conversion import strip_markdown
from kadi.lib.resources.core import create_resource
from kadi.lib.resources.core import delete_resource
from kadi.lib.resources.core import purge_resource
from kadi.lib.resources.core import restore_resource
from kadi.lib.resources.core import signal_resource_change
from kadi.lib.resources.core import update_resource
from kadi.lib.revisions.core import create_revision

from .models import Template
from .models import TemplateState
from .models import TemplateType
from .models import TemplateVisibility


def _check_template_data(template_type, template_data):
    # Basic structure check of the template data.
    if template_type == TemplateType.RECORD:
        return isinstance(template_data, dict)

    if template_type == TemplateType.EXTRAS:
        return isinstance(template_data, list)

    return False


def create_template(
    *,
    identifier,
    title,
    type,
    data,
    creator=None,
    description="",
    visibility=TemplateVisibility.PRIVATE,
    state=TemplateState.ACTIVE,
):
    """Create a new template.

    Uses :func:`kadi.lib.resources.core.create_resource`.

    :param identifier: See :attr:`.Template.identifier`.
    :param title: See :attr:`.Template.title`.
    :param type: See :attr:`.Template.type`.
    :param data: See :attr:`.Template.data`.
    :param creator: (optional) The creator of the template. Defaults to the current
        user.
    :param description: (optional) See :attr:`.Template.description`.
    :param visibility: (optional) See :attr:`.Template.visibility`.
    :param state: (optional) See :attr:`.Template.state`.
    :return: See :func:`kadi.lib.resources.core.create_resource`.
    """
    creator = creator if creator is not None else current_user

    if not _check_template_data(type, data):
        return None

    return create_resource(
        Template,
        creator=creator,
        identifier=identifier,
        title=title,
        type=type,
        data=data,
        description=description,
        plain_description=strip_markdown(description),
        visibility=visibility,
        state=state,
    )


def update_template(template, data=None, user=None, **kwargs):
    r"""Update an existing template.

    Uses :func:`kadi.lib.resources.core.update_resource`.

    :param template: The template to update.
    :param data: (optional) See :attr:`.Template.data`.
    :param user: (optional) The user who triggered the update. Defaults to the current
        user.
    :param \**kwargs: Keyword arguments that will be passed to
        :func:`kadi.lib.resources.update_resource`. See also :func:`create_template`.
    :return: See :func:`kadi.lib.resources.core.update_resource`.
    """
    user = user if user is not None else current_user

    if data is not None:
        if not _check_template_data(template.type, data):
            return False

        kwargs["data"] = data

    if "description" in kwargs:
        kwargs["plain_description"] = strip_markdown(kwargs["description"])

    return update_resource(template, user=user, **kwargs)


def delete_template(template, user=None):
    """Delete an existing template.

    Uses :func:`kadi.lib.resources.core.delete_resource`.

    :param template: The template to delete.
    :param user: (optional) The user who triggered the deletion. Defaults to the current
        user.
    """
    user = user if user is not None else current_user
    delete_resource(template, user=user)


def restore_template(template, user=None):
    """Restore a deleted template.

    Uses :func:`kadi.lib.resources.core.restore_resource`.

    :param template: The template to restore.
    :param user: (optional) The user who triggered the restoration. Defaults to the
        current user.
    """
    user = user if user is not None else current_user
    restore_resource(template, user=user)


def purge_template(template):
    """Purge an existing template.

    Uses :func:`kadi.lib.resources.core.purge_resource`.

    :param template: The template to purge.
    """

    # Save references to the collections that use the template as default record
    # template before actually deleting it.
    collections = template.collections.all()

    purge_resource(template)

    # Since default record templates are also tracked as part of the collection
    # revisions, deleting the template should also trigger a new revision in all
    # corresponding collections, regardless of their state.
    revisions = []

    for collection in collections:
        revision = create_revision(collection)
        revisions.append(revision)

    db.session.commit()

    for revision in revisions:
        signal_resource_change(revision)
