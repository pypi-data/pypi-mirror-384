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
from uuid import uuid4

from celery import states
from celery.signals import task_postrun
from celery.signals import task_prerun
from flask import current_app

from kadi.ext.celery import celery
from kadi.ext.db import db
from kadi.lib.notifications.models import Notification
from kadi.lib.notifications.models import NotificationName

from .models import Task
from .models import TaskState


@task_prerun.connect
def _task_prerun(task_id, **kwargs):
    kwargs = kwargs["kwargs"]

    if "_meta" in kwargs and kwargs["_meta"].get("keep", False):
        task = Task.query.get(task_id)

        if task is not None and task.state == TaskState.PENDING:
            task.state = TaskState.RUNNING
            db.session.commit()


@task_postrun.connect
def _task_postrun(task_id, state, **kwargs):
    kwargs = kwargs["kwargs"]

    if "_meta" in kwargs and kwargs["_meta"].get("keep", False):
        task = Task.query.get(task_id)

        if task is not None and task.state == TaskState.RUNNING:
            if state == states.SUCCESS:
                task.state = TaskState.SUCCESS
                task.update_progress(100)
            elif state == states.REVOKED:
                task.state = TaskState.REVOKED
            else:
                task.state = TaskState.FAILURE

            db.session.commit()


def launch_task(name, args=None, kwargs=None, user=None, keep=False, notify=False):
    """Launch a new Celery task by name.

    Note that this function issues one or more database commits if ``keep`` is ``True``.

    :param name: The name of the task.
    :param args: (optional) Positional arguments to pass to the task as list. All
        arguments need to be JSON serializable.
    :param kwargs: (optional) Keyword arguments to pass to the task as dictionary. All
        arguments need to be JSON serializable.
    :param user: (optional) The user who started the task.
    :param keep: (optional) Flag indicating whether a reference to the task should be
        kept in the database until its expiration date (via the periodic cleanup task).
        See also :class:`.Task`.
    :param notify: (optional) Flag indicating whether the user who started the task
        should be notified about its status, in which case a new instance of
        :class:`.Notification` of type ``"task_status"`` will be created for that user.
        The data of this notification consists of a dictionary, containing the ID of the
        task as ``"task_id"``. This requires that a valid user is passed and ``keep``
        must be ``True`` as well.
    :return: A boolean indicating whether the task was launched successfully or not if
        ``keep`` is ``False``. A new :class:`.Task` object or ``None`` if ``keep`` is
        ``True``.
    """
    args = args if args is not None else []
    kwargs = kwargs if kwargs is not None else {}

    if name not in celery.tasks:
        current_app.logger.error(f"Task '{name}' is not registered.")
        return None if keep else False

    task = None

    if keep:
        task = Task.create(creator=user, name=name, args=args, kwargs=kwargs)
        db.session.commit()

    kwargs["_meta"] = {
        "user": user.id if user is not None else None,
        "keep": keep,
        "notify": notify,
    }

    try:
        task_id = str(task.id) if task else str(uuid4())
        celery.send_task(name, args=tuple(args), kwargs=kwargs, task_id=task_id)
    except Exception as e:
        current_app.logger.exception(e)

        if keep:
            db.session.delete(task)
            db.session.commit()
            return None

        return False

    if user is not None and keep and notify:
        Notification.create(
            user=user, name=NotificationName.TASK_STATUS, data={"task_id": str(task.id)}
        )
        db.session.commit()

    return task if keep else True
