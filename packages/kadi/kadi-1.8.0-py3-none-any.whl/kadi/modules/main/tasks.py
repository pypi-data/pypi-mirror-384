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
from celery.exceptions import SoftTimeLimitExceeded
from flask import current_app

import kadi.lib.constants as const
from kadi.ext.celery import celery
from kadi.lib.oauth.utils import clean_auth_codes
from kadi.lib.resources.utils import clean_resources
from kadi.lib.tasks.utils import clean_tasks
from kadi.modules.accounts.utils import clean_users
from kadi.modules.records.utils import clean_files


@celery.task(name=const.TASK_PERIODIC_CLEANUP, soft_time_limit=const.ONE_HOUR)
def _periodic_cleanup_task(**kwargs):
    try:
        clean_users(inside_task=True)
        clean_resources(inside_task=True)
        clean_files(inside_task=True)
        clean_tasks(inside_task=True)
        clean_auth_codes(inside_task=True)

    except SoftTimeLimitExceeded as e:
        current_app.logger.exception(e)
        return False

    return True
