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
from flask_login import current_user

import kadi.lib.constants as const
from kadi.ext.celery import celery
from kadi.ext.db import db
from kadi.lib.exceptions import KadiFilesizeMismatchError
from kadi.lib.tasks.core import launch_task
from kadi.lib.tasks.models import Task
from kadi.lib.tasks.models import TaskState

from .core import purge_record
from .models import Record
from .models import RecordState
from .models import Upload
from .models import UploadState
from .uploads import merge_chunk_data


@celery.task(name=const.TASK_MERGE_CHUNKS, soft_time_limit=const.ONE_HOUR, bind=True)
def _merge_chunks_task(self, upload_id, **kwargs):
    task = Task.query.get(self.request.id)
    upload = Upload.query.get(upload_id)

    file = None
    error_msg = "Error creating or updating file."

    # Check if the upload is still ready to be processed at this point.
    if upload is None or upload.state != UploadState.PROCESSING:
        task.state = TaskState.FAILURE
        task.result = {"error": error_msg}
    else:
        try:
            file = merge_chunk_data(upload)

            if file is not None:
                task.result = {"file": str(file.id)}
            else:
                task.state = TaskState.FAILURE
                task.result = {"error": error_msg}

        # Catches time limit exceeded exceptions as well.
        except Exception as e:
            db.session.rollback()
            task.state = TaskState.FAILURE

            if isinstance(e, KadiFilesizeMismatchError):
                task.result = {"error": str(e)}
            else:
                current_app.logger.exception(e)
                task.result = {"error": "Internal server error."}

    db.session.commit()
    return str(file.id) if file is not None else None


def start_merge_chunks_task(upload, user=None):
    """Merge the chunks of a local file upload in a background task.

    Uses :func:`kadi.modules.records.uploads.merge_chunk_data`. The created task will be
    kept in the database.

    Note that this function issues one or more database commits.

    :param upload: The upload that the chunks belong to.
    :param user: (optional) The user who started the task. Defaults to the current user.
    :return: The new task object if the task was started successfully, ``None``
        otherwise.
    """
    user = user if user is not None else current_user

    return launch_task(
        const.TASK_MERGE_CHUNKS, args=[str(upload.id)], user=user, keep=True
    )


@celery.task(name=const.TASK_PURGE_RECORD, soft_time_limit=const.ONE_HOUR)
def _purge_record_task(record_id, **kwargs):
    record = Record.query.get(record_id)

    try:
        purge_record(record)

    # Catches time limit exceeded exceptions as well.
    except Exception as e:
        current_app.logger.exception(e)
        db.session.rollback()

        # In case the state of the record was already changed, we reset it so another
        # attempt can be made to purge it (including the periodic cleanup task).
        record.state = RecordState.DELETED
        db.session.commit()

        return False

    return True


def start_purge_record_task(record):
    """Purge an existing record in a background task.

    Uses :func:`kadi.modules.records.core.purge_record`.

    :param record: The record to purge.
    """
    return launch_task(const.TASK_PURGE_RECORD, args=[record.id])
