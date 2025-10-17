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

import kadi.lib.constants as const
from kadi.ext.celery import celery
from kadi.lib.tasks.core import launch_task

from .core import send_mail


@celery.task(name=const.TASK_SEND_MAIL, max_retries=5, bind=True)
def _send_mail_task(
    self,
    *,
    subject,
    message,
    to_addresses,
    from_address=None,
    cc=None,
    bcc=None,
    attachments=None,
    reply_to=None,
    html_message=None,
    headers=None,
    **kwargs,
):
    try:
        return send_mail(
            subject=subject,
            message=message,
            to_addresses=to_addresses,
            from_address=from_address,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            reply_to=reply_to,
            html_message=html_message,
            headers=headers,
        )

    except ConnectionRefusedError as e:
        self.retry(countdown=60, exc=e)

    # Catches retry exceeded exceptions as well.
    except Exception as e:
        current_app.logger.exception(e)
        return 0


def start_send_mail_task(
    *,
    subject,
    message,
    to_addresses,
    from_address=None,
    cc=None,
    bcc=None,
    attachments=None,
    reply_to=None,
    html_message=None,
    headers=None,
):
    """Send a mail in a background task.

    See :func:`kadi.lib.mails.core.send_mail` for the possible parameters.

    In case the connection to the mail server fails, the task will be retried every 60
    seconds until a maximum defined in ``CELERY_ANNOTATIONS`` in the application's
    configuration is reached. Other errors will cause the task to fail, however.

    :return: ``True`` if the task was started successfully, ``False`` otherwise. Note
        that the task being started successfully does not necessarily mean that the
        email will be sent successfully as well.
    """
    return launch_task(
        const.TASK_SEND_MAIL,
        kwargs={
            "subject": subject,
            "message": message,
            "to_addresses": to_addresses,
            "from_address": from_address,
            "cc": cc,
            "bcc": bcc,
            "attachments": attachments,
            "reply_to": reply_to,
            "html_message": html_message,
            "headers": headers,
        },
    )
