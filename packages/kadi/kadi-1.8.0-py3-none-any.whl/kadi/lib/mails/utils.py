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
from flask import render_template

import kadi.lib.constants as const

from .tasks import start_send_mail_task


def send_email_confirmation_mail(identity, email=None):
    """Send an email confirmation mail in a background task.

    Uses :func:`kadi.lib.mails.tasks.start_send_mail_task` to send the mail.

    :param identity: The identity of the user whose email should be confirmed.
    :param email: (optional) The email address to use as the recipient address and to
        include in the email confirmation token. Defaults to the email address of the
        given identity.
    :return: See :func:`kadi.lib.mails.tasks.start_send_mail_task`.
    """
    email = email if email is not None else identity.email

    token = identity.get_email_confirmation_token(
        const.JWT_MAIL_EXPIRES_IN, email=email
    )
    message = render_template(
        "mails/email_confirmation.txt",
        displayname=identity.user.displayname,
        token=token,
        expires_in=const.JWT_MAIL_EXPIRES_IN,
    )
    subject_header = current_app.config["MAIL_SUBJECT_HEADER"]

    return start_send_mail_task(
        subject=f"[{subject_header}] Email confirmation",
        to_addresses=[email],
        message=message,
    )


def send_password_reset_mail(identity):
    """Send a password reset mail in a background task.

    Uses :func:`kadi.lib.mails.tasks.start_send_mail_task` to send the mail.

    :param identity: The local identity of the user whose password should be reset.
    :return: See :func:`kadi.lib.mails.tasks.start_send_mail_task`.
    """
    token = identity.get_password_reset_token(const.JWT_MAIL_EXPIRES_IN)
    message = render_template(
        "mails/password_reset.txt",
        displayname=identity.user.displayname,
        token=token,
        expires_in=const.JWT_MAIL_EXPIRES_IN,
    )
    subject_header = current_app.config["MAIL_SUBJECT_HEADER"]

    return start_send_mail_task(
        subject=f"[{subject_header}] Password reset request",
        to_addresses=[identity.email],
        message=message,
    )


def send_test_mail(user):
    """Send a test mail in a background task.

    Uses :func:`kadi.lib.mails.tasks.start_send_mail_task` to send the mail.

    :param user: The user to send the test email to.
    :return: See :func:`kadi.lib.mails.tasks.start_send_mail_task`.
    """
    message = render_template("mails/test_email.txt", displayname=user.displayname)
    subject_header = current_app.config["MAIL_SUBJECT_HEADER"]

    return start_send_mail_task(
        subject=f"[{subject_header}] Test email",
        to_addresses=[user.identity.email],
        message=message,
    )
