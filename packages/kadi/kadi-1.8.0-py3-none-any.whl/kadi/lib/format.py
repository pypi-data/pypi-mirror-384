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
from datetime import timezone

from flask_babel import format_decimal
from flask_babel import gettext as _

from kadi.lib.utils import utcnow


def duration(seconds):
    """Create a human-readable, translated duration string from an amount of seconds.

    Note that locale-aware translations are only supported when having an active request
    context.

    :param seconds: The amount of seconds.
    :return: The formatted duration string.
    """
    if seconds <= 0:
        return "0 {}".format(_("seconds"))

    units = [
        (_("second"), _("seconds"), 60),
        (_("minute"), _("minutes"), 60),
        (_("hour"), _("hours"), 24),
        (_("day"), _("days"), 7),
        (_("week"), _("weeks"), None),
    ]

    result = ""
    current_value = new_value = seconds

    for singular, plural, factor in units:
        if factor is not None:
            new_value = current_value // factor
            current_value = current_value % factor

        if current_value > 0:
            unit = singular

            if current_value > 1:
                unit = plural

            result = f"{current_value} {unit}{', ' + result if result else ''}"

        current_value = new_value

    return result


def filesize(num_bytes):
    """Create a human-readable, localized file size from a given amount of bytes.

    Based on Jinja's ``filesizeformat`` filter. Note that locale-aware localization is
    only supported when having an active request context.

    :param num_bytes: The amount of bytes as a string or number.
    :return: The formatted file size string.
    """
    num_bytes = int(float(num_bytes))
    base = 1_000

    if num_bytes == 1:
        return "1 Byte"

    if num_bytes < base:
        return f"{num_bytes} Bytes"

    unit = 1

    for i, prefix in enumerate(["kB", "MB", "GB", "TB", "PB"]):
        unit = base ** (i + 2)

        if num_bytes < unit:
            break

    formatted_size = format_decimal(f"{base * num_bytes / unit:.1f}")
    return f"{formatted_size} {prefix}"


def timestamp(date_time=None, include_micro=False):
    """Build a UTC timestamp from a specific date and time.

    The timestamp will be in the form of ``"YYYYMMDDHHmmss"``.

    :param date_time: (optional) A datetime object as specified in Python's ``datetime``
        module. Defaults to the current time.
    :param include_micro: (optional) Flag indicating whether to include microseconds in
        the timestamp as well or not.
    :return: The formatted timestamp string.
    """
    fmt = "%Y%m%d%H%M%S"

    if include_micro:
        fmt += "%f"

    if date_time is None:
        date_time = utcnow()

    return date_time.astimezone(timezone.utc).strftime(fmt)
