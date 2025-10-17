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
import math
import operator
import os
from collections import namedtuple
from contextlib import contextmanager
from contextlib import redirect_stderr
from datetime import datetime
from datetime import timezone
from importlib import import_module
from urllib.parse import urlparse

from flask import current_app
from flask import json


class SimpleReprMixin:
    """Mixin to add a simple implementation of ``__repr__`` to a class.

    The provided implementation uses all instance or class attributes specified in the
    ``Meta.representation`` attribute of the inheriting class. It should be a list of
    strings specifying the attributes to use in the representation.

    **Example:**

    .. code-block:: python3

        class Foo:
            class Meta:
                representation = ["bar", "baz"]

            bar = 1

            baz = 2
    """

    def __repr__(self):
        attrs = ", ".join(
            f"{attr}={getattr(self, attr)!r}" for attr in self.Meta.representation
        )
        return f"{self.__class__.__name__}({attrs})"


class _StringEnumMeta(type):
    def __new__(cls, name, bases, class_dict):
        values_key = "__values__"

        if values_key not in class_dict:
            class_dict[values_key] = []

        for value in class_dict[values_key]:
            class_dict[value.upper()] = value

        return super().__new__(cls, name, bases, class_dict)


class StringEnum(metaclass=_StringEnumMeta):
    """Custom enum-like class that uses regular strings as values.

    An inheriting class needs to specify a ``__values__`` attribute for all possible
    enum string values. Each value will be added as a class attribute using its
    respective value as key in uppercase.

    **Example:**

    .. code-block:: python3

        class Foo:
            __values__ = ["bar"]
    """


@contextmanager
def suppress_stderr():
    """Context manager to suppress output written to stderr."""

    # pylint: disable=unspecified-encoding
    with open(os.devnull, mode="w") as f:
        with redirect_stderr(f):
            yield


def named_tuple(tuple_name, **kwargs):
    r"""Convenience function to build a ``namedtuple`` from keyword arguments.

    :param tuple_name: The name of the tuple.
    :param \**kwargs: The keys and values of the tuple.
    :return: The ``namedtuple`` instance.
    """
    NamedTuple = namedtuple(tuple_name, list(kwargs))
    return NamedTuple(*list(kwargs.values()))


def compare(left, op, right):
    """Compare two values with a given operator.

    :param left: The left value.
    :param op: One of ``"=="``, ``"!="``, ``">"``, ``"<"``, ``">="`` or ``"<="``.
    :param right: The right value.
    :return: The boolean result of the comparison.
    """
    ops = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
    }
    return ops[op](left, right)


def rgetattr(obj, name, default=None):
    """Get a nested attribute of an object.

    :param obj: The object to get the attribute from.
    :param name: The name of the attribute in the form of ``"foo.bar.baz"``.
    :param default: (optional) The default value to return if the attribute could not be
        found.
    :return: The attribute or the default value if it could not be found.
    """
    attr = obj

    for _name in name.split("."):
        try:
            attr = getattr(attr, _name)
        except AttributeError:
            return default

    return attr


def get_class_by_name(name):
    """Get a class given its name.

    :param name: The complete name of the class in the form of ``"foo.bar.Baz"``.
    :return: The class or ``None`` if it could not be found.
    """
    names = name.rsplit(".", 1)

    if len(names) <= 1:
        return None

    try:
        mod = import_module(names[0])
    except ImportError:
        return None

    return getattr(mod, names[1], None)


def utcnow():
    """Create a timezone aware datetime object of the current time in UTC.

    :return: A datetime object as specified in Python's ``datetime`` module.
    """
    return datetime.now(timezone.utc)


def compact_json(data, ensure_ascii=False, sort_keys=True):
    """Serialize data to a compact JSON formatted string.

    Uses the JSON encoder provided by Flask, which can deal with some additional types.

    :param data: The data to serialize.
    :param ensure_ascii: (optional) Whether to escape non-ASCII characters.
    :param sort_keys: (optional) Whether to sort the output of dictionaries by key.
    :return: The JSON formatted string.
    """
    return json.dumps(
        data, ensure_ascii=ensure_ascii, sort_keys=sort_keys, separators=(",", ":")
    )


def formatted_json(data, ensure_ascii=False, sort_keys=True):
    """Serialize data to a user-readable JSON formatted string.

    Uses the JSON encoder provided by Flask, which can deal with some additional types.

    :param data: The data to serialize.
    :param ensure_ascii: (optional) Whether to escape non-ASCII characters.
    :param sort_keys: (optional) Whether to sort the output of dictionaries by key.
    :return: The JSON formatted string.
    """
    return json.dumps(data, ensure_ascii=ensure_ascii, sort_keys=sort_keys, indent=2)


def is_special_float(value):
    """Check if a float value is a special value, i.e. ``nan`` or ``inf``.

    :param value: The float value to check.
    :return: ``True`` if the value is a special float value, ``False`` otherwise.
    """
    return math.isnan(value) or math.isinf(value)


def is_iterable(value, include_string=False):
    """Check if a value is an iterable.

    :param value: The value to check.
    :param include_string: (optional) Flag indicating whether a string value should be
        treated as a valid iterable or not.
    :return: ``True`` if the value is iterable, ``False`` otherwise.
    """
    if not include_string and isinstance(value, str):
        return False

    try:
        iter(value)
    except TypeError:
        return False

    return True


def is_quoted(value):
    """Check if a string value is quoted, i.e. surrounded by double quotes.

    :param value: The string value to check.
    :return: ``True`` if the value is quoted, ``False`` otherwise.
    """
    return value.startswith('"') and value.endswith('"') and len(value) >= 2


def is_http_url(value):
    """Check if a string represent a valid HTTP URL.

    :param value: The string value to check.
    :return: ``True`` if the value represents a HTTP URL, ``False`` otherwise.
    """
    uri = urlparse(value)
    return bool(uri.netloc) and uri.scheme in {"http", "https"}


def find_dict_in_list(dict_list, key, value):
    """Find a dictionary with a specific key and value in a list.

    :param dict_list: A list of dictionaries to search.
    :param key: The key to search for.
    :param value: The value to search for.
    :return: The dictionary or ``None`` if it was not found.
    """
    for item in dict_list:
        if key in item and item[key] == value:
            return item

    return None


def flatten_list(values):
    """Flatten a list of lists.

    Flattens a list containing single values or nested lists. Multiple layers of nested
    lists are not supported.

    :param values: List containing single values or nested lists.
    :return: The flattened list.
    """
    flattened_result = []

    for value in values:
        if isinstance(value, list):
            flattened_result += value
        else:
            flattened_result.append(value)

    return flattened_result


def as_list(value):
    """Wrap a value inside a list if the given value is not a list already.

    :param value: The value to potentially wrap.
    :return: The original or wrapped value. If the given value is ``None``, the value
        will always be returned as is.
    """
    return value if isinstance(value, list) else [value] if value else None


def has_capabilities(*capabilities):
    """Check if the current Kadi instance has all given capabilities.

    :param capabilities: One or more capabilities to check.
    :return: ``True`` if all given capabilities are available, ``False`` otherwise.
    """
    satisfied_capabilities = [
        c in current_app.config["CAPABILITIES"] for c in capabilities
    ]
    return all(satisfied_capabilities)
