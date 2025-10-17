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
from datetime import timedelta

from flask import current_app

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.utils import utcnow

from .models import Task
from .models import TaskState


def clean_tasks(inside_task=False):
    """Clean all expired, finished tasks.

    Note that this function issues a database commit.

    :param inside_task: (optional) A flag indicating whether the function is executed in
        a task. In that case, additional information will be logged.
    """
    expiration_date = utcnow() - timedelta(seconds=const.FINISHED_TASKS_MAX_AGE)
    tasks = Task.query.filter(
        Task.state.in_([TaskState.REVOKED, TaskState.SUCCESS, TaskState.FAILURE]),
        Task.last_modified < expiration_date,
    )

    if inside_task and tasks.count() > 0:
        current_app.logger.info(f"Cleaning {tasks.count()} finished tasks(s).")

    for task in tasks:
        db.session.delete(task)

    db.session.commit()
