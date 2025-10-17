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
from kadi.vendor.django_mail.mail_backends import EmailBackend
from kadi.vendor.django_mail.mail_message import EmailMultiAlternatives


def send_mail(
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
    """Send an email to one or multiple recipients.

    Uses the configuration values ``SMTP_HOST``, ``SMTP_PORT``, ``SMTP_USERNAME``,
    ``SMTP_PASSWORD``, ``SMTP_TIMEOUT`` and ``SMTP_USE_TLS`` set in the application's
    configuration for the connection.

    :param subject: The subject of the email.
    :param message: The plain text message of the email.
    :param to_addresses: A list of recipient addresses.
    :param from_address: (optional) The sender's email address. Defaults to the address
        set in ``MAIL_NO_REPLY`` in the current application's configuration.
    :param cc: (optional) A list of recipient addresses used in the "CC" header when
        sending the email.
    :param bcc: (optional) A list of recipient addresses used in the "BCC" header when
        sending the email.
    :param attachments: (optional) A list of attachments to put on the message. The list
        has to consist of triples in the form of ``(filename, content, mimetype)``. The
        content can either be a string or bytes object, while the MIME type will be
        guessed based on the given filename if omitted (i.e. set to ``None``).
    :param reply_to: (optional) A list of recipient addresses used in the "Reply-To"
        header when sending the email.
    :param html_message: (optional) An HTML message of the email as alternative to the
        plain text version.
    :param headers: (optional) A dictionary of additional headers to put on the message,
        mapping header names to their respective values.
    :return: The number of emails that were sent successfully.
    :raises: ConnectionRefusedError: If no connection with the SMTP server could be
        established.
    """
    if from_address is None:
        from_address = current_app.config["MAIL_NO_REPLY"]

    with EmailBackend() as connection:
        mail = EmailMultiAlternatives(
            subject=subject,
            body=message,
            to=to_addresses,
            from_email=from_address,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            reply_to=reply_to,
            headers=headers,
            connection=connection,
        )

        if html_message is not None:
            mail.attach_alternative(html_message, const.MIMETYPE_HTML)

        return mail.send()
