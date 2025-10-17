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
from urllib.parse import urlparse

from flask import current_app
from flask import json
from markdown_it import MarkdownIt
from markupsafe import Markup
from marshmallow.utils import from_iso_datetime
from mdit_py_plugins.texmath import texmath_plugin


def strip(value):
    """Strip all surrounding whitespaces in a string.

    :param value: The string to strip.
    :return: The stripped string or the original input if it was not a string.
    """
    if isinstance(value, str):
        return value.strip()

    return value


def normalize(value):
    """Normalize all and strip surrounding whitespaces in a string.

    :param value: The string to normalize.
    :return: The normalized string or the original input if it was not a string.
    """
    if isinstance(value, str):
        return " ".join(value.split())

    return value


def normalize_uri(value):
    """Normalize a URI by lowercasing its domain name portion.

    :param value: The URI to normalize as string.
    :return: The normalized URI or the original input if it was not a string.
    """
    if isinstance(value, str):
        uri = urlparse(value)
        return uri._replace(netloc=uri.netloc.lower()).geturl()

    return value


def lower(value):
    """Lowercase all characters in a string.

    :param value: The string to lowercase.
    :return: The lowercased string or the original input if it was not a string.
    """
    if isinstance(value, str):
        return value.lower()

    return value


def truncate(value, length):
    """Truncate a string based on a given length.

    :param value: The string to truncate.
    :param length: The maximum length of the string.
    :return: The truncated string or the original input if it was not a string.
    """
    if isinstance(value, str) and len(value) > length:
        return f"{value[:length]}..."

    return value


def recode(value, from_encoding="utf-8", to_encoding="utf-8"):
    """Change the encoding of a string.

    :param value: The string value.
    :param from_encoding: (optional) The original encoding of the string.
    :param to_encoding: (optional) The target encoding of the string.
    :return: The newly encoded string or the original input if it was not a string or
        the recoding failed.
    """
    try:
        if isinstance(value, str):
            value = value.encode(from_encoding).decode(to_encoding)
    except UnicodeDecodeError:
        pass

    return value


def clamp(value, min_value, max_value):
    """Clamp a numeric value to the inclusive range of the given min and max values.

    :param min_value: The minumum value.
    :param max_value: The maximum value.
    :return: The clamped value or the original input if it was not a numeric value.
    """
    if isinstance(value, (int, float)):
        return min(max(value, min_value), max_value)

    return value


def none(value):
    """Return ``None`` if a given value is falsy.

    :param value: A value to check for truthness.
    :return: The unmodified value or ``None`` if it is falsy.
    """
    if not value:
        return None

    return value


def empty_str(value):
    """Return an empty string if a given value is ``None``.

    :param value: A value to check for being ``None``.
    :return: The unmodified value or an empty string if it is ``None``.
    """
    if value is None:
        return ""

    return value


def markdown_to_html(value):
    """Render a markdown string as HTML.

    Note that manually entered HTML will be left intact, as it will be escaped
    accordingly.

    :param value: The string to render.
    :return: The rendered string or the original input if it was not a string or could
        not be rendered.
    """
    if isinstance(value, str):
        md = MarkdownIt("js-default").use(texmath_plugin)

        try:
            value = md.render(value)
        except Exception as e:
            current_app.logger.debug(e, exc_info=True)

    return value


def strip_markdown(value):
    """Strip a string of its markdown directives and normalize its whitespaces.

    Note that not all directives may be stripped, since some may not be supported by the
    markdown renderer used in :func:`markdown_to_html`.

    :param value: The string to strip.
    :return: The stripped string or the original input if it was not a string.
    """
    if isinstance(value, str):
        value = markdown_to_html(value)
        return Markup(value).striptags()

    return value


def parse_datetime_string(value):
    """Parse a datetime string.

    :param value: The datetime string to parse in ISO 8601 format.
    :return: A timezone aware datetime object in UTC as specified in Python's
        ``datetime`` module or ``None`` if the given string was not a valid datetime
        string.
    """
    try:
        # Marshmallow's parsing is much more robust than the standard library parsing
        # utilities, at least for older Python versions.
        return from_iso_datetime(value).astimezone(timezone.utc)
    except ValueError:
        return None


def parse_boolean_string(value):
    """Parse a boolean string.

    The given string is parsed based on typical values used for thruthness, including
    ``True``, ``"true"``, ``"t"``, ``"yes"``, ``"y"``, ``"on"`` and ``"1"`` (case
    insensitive for all string values), instead of using Python's ``bool`` conversion.
    All other values are considered false.

    :param value: The boolean string to parse.
    :return: ``True`` if the given string is considered truthy, ``False`` otherwise.
    """
    if isinstance(value, str):
        value = value.lower()

    return value in {True, "true", "t", "yes", "y", "on", "1"}


def parse_json_object(value):
    """Parse a JSON object string as a dictionary.

    :param value: The JSON object string to parse.
    :return: The parsed dictionary or an empty dictionary if the given string was not a
        valid JSON object.
    """
    try:
        value = json.loads(value)
    except:
        return {}

    return value if isinstance(value, dict) else {}
