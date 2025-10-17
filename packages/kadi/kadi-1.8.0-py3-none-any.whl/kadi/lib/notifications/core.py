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
from flask import current_app
from flask_babel import gettext as _

from kadi.ext.db import db
from kadi.lib.plugins.core import run_hook
from kadi.lib.tasks.models import Task
from kadi.lib.tasks.models import TaskState

from .models import NotificationName


def create_notification_data(notification):
    """Create notification data suitable for presenting it to a client.

    Uses the :func:`kadi.plugins.spec.kadi_get_background_task_notification` plugin
    hook for handling task status notifications.

    :param notification: A :class:`.Notification` object to use for creating the
        notification data.
    :return: A tuple containing the title and the HTML body of the notification.
    """
    title = body = notification.name

    # Task status notifications.
    if notification.name == NotificationName.TASK_STATUS:
        title = _("Task status")
        task = Task.query.filter(Task.id == notification.data["task_id"]).first()

        if task is None:
            return title, _("Task no longer exists.")

        if task.state == TaskState.PENDING:
            body = _("Waiting for available resources...")
        elif task.state == TaskState.RUNNING:
            body = _("Task running...")
        elif task.state == TaskState.SUCCESS:
            body = _("Task succeeded.")
        elif task.state == TaskState.FAILURE:
            body = _("Task failed.")
        elif task.state == TaskState.REVOKED:
            body = _("Task revoked.")

        try:
            data = run_hook("kadi_get_background_task_notification", task=task)

            if isinstance(data, tuple) and len(data) == 2:
                title = data[0] if data[0] is not None else title
                body = data[1] if data[1] is not None else body

        except Exception as e:
            current_app.logger.exception(e)

        title = f"{title} ({task.pretty_state})"

    return title, body


def dismiss_notification(notification):
    """Dismiss a notification.

    If the notification is of type ``"task_status"``, the referenced task will be
    revoked as well.

    :param notification: The :class:`.Notification` to dismiss.
    """
    if notification.name == NotificationName.TASK_STATUS:
        task = Task.query.filter(Task.id == notification.data["task_id"]).first()

        if task is not None:
            task.revoke()

    db.session.delete(notification)
