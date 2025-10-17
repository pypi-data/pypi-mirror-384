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
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import update_object
from kadi.lib.favorites.core import delete_favorites
from kadi.lib.permissions.core import add_role
from kadi.lib.permissions.utils import delete_roles
from kadi.lib.permissions.utils import initialize_roles
from kadi.lib.plugins.core import run_hook
from kadi.lib.revisions.core import create_revision
from kadi.lib.revisions.core import delete_revisions
from kadi.lib.tags.models import TaggingMixin


def signal_resource_change(revision):
    """Convenience function to signal the creation or change of a resource.

    Uses the :func:`kadi.plugins.spec.kadi_post_resource_change` plugin hook.

    Note that this function may issue a database rollback.

    :param revision: The revision that was created after a resource was created or
        changed. May also be ``None``, in which case the plugin hook is skipped.
    """
    if revision is None:
        return

    try:
        run_hook("kadi_post_resource_change", revision=revision)
    except Exception as e:
        current_app.logger.exception(e)
        db.session.rollback()


def create_resource(model, tags=None, creator=None, **kwargs):
    r"""Convenience function to create a new resource.

    Note that this function issues a database commit or rollback.

    :param model: The model that represents the type of the new resource. One of
        :class:`.Record`, :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param tags: (optional) A list of tags to tag the resource with if it inherits from
        :class:`.TaggingMixin`.
    :param creator: (optional) The creator of the resource. Defaults to the current
        user.
    :param \**kwargs: Keyword arguments that will be used to intialize the data of the
        new resource.
    :return: The created resource or ``None`` if the resource could not be created.
    """
    creator = creator if creator is not None else current_user

    resource = model.create(creator=creator, **kwargs)

    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return None

    if (
        tags is not None
        and isinstance(resource, TaggingMixin)
        and not resource.set_tags(tags)
    ):
        db.session.rollback()
        return None

    initialize_roles(model.__tablename__, resource.id)
    add_role(creator, model.__tablename__, resource.id, "admin")

    revision = create_revision(resource, user=creator)
    db.session.commit()

    signal_resource_change(revision)

    return resource


def update_resource(resource, tags=None, user=None, **kwargs):
    r"""Convenience function to update an existing resource.

    Note that this function may issue a database commit or rollback.

    :param resource: The resource to update. An instance of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param tags: (optional) A list of tags to tag the resource with if it inherits from
        :class:`.TaggingMixin`.
    :param user: (optional) The user who triggered the update. Defaults to the current
        user.
    :param \**kwargs: Keyword arguments that will be passed to
        :func:`kadi.lib.db.update_object`.
    :return: ``True`` if the resource was updated successfully, ``False`` otherwise.
    """
    user = user if user is not None else current_user

    if resource.state != const.MODEL_STATE_ACTIVE:
        return False

    update_object(resource, **kwargs)

    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return False

    if (
        tags is not None
        and isinstance(resource, TaggingMixin)
        and not resource.set_tags(tags)
    ):
        db.session.rollback()
        return False

    revision = create_revision(resource, user=user)
    db.session.commit()

    signal_resource_change(revision)

    return True


def delete_resource(resource, user=None):
    """Convenience function to delete an existing resource.

    This will perform a soft deletion, i.e. only the resource's state will be changed.

    Note that this function issues a database commit.

    :param resource: The resource to delete. An instance of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param user: (optional) The user who triggered the deletion. Defaults to the current
        user.
    """
    user = user if user is not None else current_user

    revision = None

    if resource.state == const.MODEL_STATE_ACTIVE:
        resource.state = const.MODEL_STATE_DELETED
        revision = create_revision(resource, user=user)

    db.session.commit()

    signal_resource_change(revision)


def restore_resource(resource, user=None):
    """Convenience function to restore a deleted resource.

    Note that this function issues a database commit.

    :param resource: The resource to restore. An instance of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param user: (optional) The user who triggered the restoration. Defaults to the
        current user.
    """
    user = user if user is not None else current_user

    revision = None

    if resource.state == const.MODEL_STATE_DELETED:
        resource.state = const.MODEL_STATE_ACTIVE
        revision = create_revision(resource, user=user)

    db.session.commit()

    signal_resource_change(revision)


def purge_resource(resource):
    """Convenience function to purge an existing resource.

    This will completely delete the resource from the database.

    Note that this function issues a database commit.

    :param resource: The resource to purge. An instance of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    """
    delete_revisions(resource)
    delete_roles(resource.__class__.__tablename__, resource.id)
    delete_favorites(resource.__class__.__tablename__, resource.id)

    db.session.delete(resource)
    db.session.commit()
