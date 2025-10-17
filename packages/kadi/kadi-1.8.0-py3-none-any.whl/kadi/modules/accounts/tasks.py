# Copyright 2023 Karlsruhe Institute of Technology
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
from celery.exceptions import SoftTimeLimitExceeded
from flask import current_app

import kadi.lib.constants as const
from kadi.ext.celery import celery
from kadi.ext.db import db
from kadi.lib.tasks.core import launch_task

from .core import merge_users
from .models import User


@celery.task(name=const.TASK_MERGE_USERS, soft_time_limit=const.ONE_HOUR)
def _merge_users_task(primary_user_id, second_user_id, **kwargs):
    primary_user = User.query.get(primary_user_id)
    secondary_user = User.query.get(second_user_id)

    if primary_user is None or secondary_user is None:
        return False

    try:
        merge_users(primary_user, secondary_user)
        db.session.commit()

    except SoftTimeLimitExceeded as e:
        current_app.logger.exception(e)
        return False

    return True


def start_merge_users_task(primary_user, secondary_user):
    """Merge two users together in a background task.

    Uses :func:`kadi.modules.accounts.core.merge_users`.

    :param primary_user: The primary user to merge the second user into.
    :param secondary_user: The secondary user to merge into the first user.
    :return: ``True`` if the task was started successfully, ``False`` otherwise.
    """
    return launch_task(
        const.TASK_MERGE_USERS, args=[primary_user.id, secondary_user.id]
    )
