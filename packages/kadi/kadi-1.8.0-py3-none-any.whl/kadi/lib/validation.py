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
import re
from functools import wraps
from uuid import UUID

from flask_babel import _

from .exceptions import KadiValidationError


def validator(exception_class):
    """Decorator to wrap a validation function.

    Handles errors of type :class:`.KadiValidationError` and reraises another
    customizable exception using the same message.

    :param exception_class: The exception to raise in case of validation failure.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except KadiValidationError as e:
                raise exception_class(str(e)) from e

        return wrapper

    return decorator


def validate_uuid(uuid_string, version=4):
    """Validate a string against a specific UUID version.

    :param uuid_string: The UUID string.
    :param version: (optional) The UUID version.
    :raises KadiValidationError: If the validation fails.
    """
    try:
        UUID(uuid_string, version=version)
    except ValueError as e:
        raise KadiValidationError(
            _("Not a valid UUIDv%(version)s.", version=version)
        ) from e


def validate_identifier(value):
    """Validate the format of an identifier.

    Identifiers can be used to give resources a human-readable, unique identification.
    An identifier is restricted to lowercase alphanumeric characters, hyphens and
    underscores.

    :param value: The identifier string.
    :raises KadiValidationError: If the validation fails.
    """
    if not re.search("^[a-z0-9-_]+$", value):
        raise KadiValidationError(
            _(
                "Not a valid identifier. Valid are lower case alphanumeric characters,"
                " hyphens and underscores."
            )
        )


def validate_mimetype(value):
    """Validate the format of a MIME type.

    A MIME type has to start with at least one alphabetical character, followed by a
    forward slash, followed by lowercase alphanumeric characters or the special
    characters ``"-"``, ``"+"`` or ``"."``.

    :param value: The MIME type string.
    :raises KadiValidationError: If the validation fails.
    """
    if not re.search("^[a-z]+/[a-z0-9-+.]+$", value):
        raise KadiValidationError(_("Not a valid MIME type."))


def validate_username(value):
    """Validate the format of a local username.

    Local usernames are restricted to lowercase alphanumeric characters with single
    hyphens or underscores in between.

    :param value: The username string.
    :raises KadiValidationError: If the validation fails.
    """
    if not re.search("^[a-z0-9]([-_]?[a-z0-9]+)*$", value):
        raise KadiValidationError(
            _(
                "Not a valid username. Valid are alphanumeric characters with single"
                " hyphens or underscores in between."
            )
        )


# Disallow the same set of characters as in "rdflib".
INVALID_IRI_CHARS = '<>" {}|\\^`'


def validate_iri(value):
    """Validate an IRI reference.

    Note that this function simply checks against a set of invalid characters.

    :param value: The IRI reference string.
    :raises KadiValidationError: If the validation fails.
    """
    for char in INVALID_IRI_CHARS:
        if char in value:
            raise KadiValidationError(_("Not a valid IRI."))
