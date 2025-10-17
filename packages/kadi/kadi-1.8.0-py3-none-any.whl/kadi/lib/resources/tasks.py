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
from flask_babel import force_locale
from flask_login import current_user

import kadi.lib.constants as const
from kadi.ext.celery import celery
from kadi.ext.db import db
from kadi.lib.conversion import parse_datetime_string
from kadi.lib.db import get_class_by_tablename
from kadi.lib.publication import publish_resource
from kadi.lib.resources.utils import purge_resources
from kadi.lib.tasks.core import launch_task
from kadi.lib.tasks.models import Task
from kadi.lib.tasks.models import TaskState
from kadi.lib.utils import utcnow
from kadi.lib.web import get_locale
from kadi.modules.accounts.models import User


@celery.task(
    name=const.TASK_PUBLISH_RESOURCE, soft_time_limit=const.ONE_HOUR, bind=True
)
def _publish_resource_task(
    self, provider, resource_type, resource_id, form_data, locale, **kwargs
):
    task = Task.query.get(self.request.id)

    # Check if the task has not already been revoked at this point.
    if task.is_revoked:
        return None

    model = get_class_by_tablename(resource_type)
    resource = model.query.get(resource_id)
    user = User.query.get(kwargs["_meta"]["user"])

    success = False

    try:
        # Since the result template may contain translatable strings and we cannot get
        # the user's locale the usual way, we instead force the locale that was given to
        # us.
        with force_locale(locale):
            success, template = publish_resource(
                provider, resource, form_data=form_data, user=user, task=task
            )

        if not success:
            task.state = TaskState.FAILURE

        task.result = {"template": template}

    # Catches time limit exceeded exceptions as well.
    except Exception as e:
        current_app.logger.exception(e)
        db.session.rollback()

        task.state = TaskState.FAILURE

    db.session.commit()
    return success


def start_publish_resource_task(
    provider, resource, form_data=None, user=None, force_locale=True
):
    """Publish a resource using a given provider in a background task.

    The created task will be kept in the database and the user who started the task will
    get notified about its current status as well.

    Note that this function issues one or more database commits.

    :param provider: The unique name of the publication provider.
    :param resource: The resource to publish. An instance of :class:`.Record` or
        :class:`.Collection`.
    :param form_data: (optional) Form data as dictionary to customize the publication
        process.
    :param user: (optional) The user who started the task. Defaults to the current user.
    :param force_locale: (optional) Flag indicating whether the current locale as
        returned by :func:`kadi.lib.web.get_locale` should be used inside the task. If
        ``False``, the default locale will be used instead.
    :return: A tuple containing a flag whether a task started by the given user is
        already pending/running, in which case no new task will be started, and either
        the new task object or ``None``, depending on whether the task was started
        successfully.
    """
    form_data = form_data if form_data is not None else {}
    user = user if user is not None else current_user

    task = user.tasks.filter(
        Task.name == const.TASK_PUBLISH_RESOURCE,
        Task.state.in_([TaskState.PENDING, TaskState.RUNNING]),
    ).first()

    if task is not None:
        return False, None

    if force_locale:
        locale = get_locale()
    else:
        locale = const.LOCALE_DEFAULT

    return True, launch_task(
        const.TASK_PUBLISH_RESOURCE,
        args=[
            provider,
            resource.__class__.__tablename__,
            resource.id,
            form_data,
            locale,
        ],
        user=user,
        keep=True,
        notify=True,
    )


@celery.task(name=const.TASK_PURGE_RESOURCES, soft_time_limit=const.ONE_HOUR)
def _purge_resources_task(timestamp, **kwargs):
    user = User.query.get(kwargs["_meta"]["user"])
    timestamp = parse_datetime_string(timestamp)

    try:
        purge_resources(user=user, timestamp=timestamp, inside_task=True)

    # Catches time limit exceeded exceptions as well.
    except Exception as e:
        current_app.logger.exception(e)
        return False

    return True


def start_purge_resources_task(user=None):
    """Purge all deleted resources created by a given user in a background task.

    :param user: (optional) The user who started the task and whose resources should be
        purged. Defaults to the current user.
    :return: A tuple containing a flag whether a task started by the given user is
        already pending/running, in which case no new task will be started, and either
        the new task object or ``None``, depending on whether the task was started
        successfully.
    """
    user = user if user is not None else current_user

    task = user.tasks.filter(
        Task.name == const.TASK_PURGE_RESOURCES,
        Task.state.in_([TaskState.PENDING, TaskState.RUNNING]),
    ).first()

    if task is not None:
        return False, None

    # Use a timestamp of the current time to ensure that only resources that were
    # deleted at the time of starting the task will be purged.
    timestamp = utcnow().isoformat()

    return True, launch_task(
        const.TASK_PURGE_RESOURCES, args=[timestamp], user=user, keep=True
    )
