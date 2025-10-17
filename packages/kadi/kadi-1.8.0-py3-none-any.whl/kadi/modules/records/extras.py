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
from copy import deepcopy
from datetime import datetime
from datetime import timezone
from functools import partial

from flask import current_app
from flask import json
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from marshmallow import ValidationError
from marshmallow import fields
from marshmallow import post_load
from marshmallow import validates_schema
from sqlalchemy.dialects.postgresql import JSONB

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.conversion import normalize
from kadi.lib.conversion import parse_datetime_string
from kadi.lib.conversion import strip
from kadi.lib.exceptions import KadiValidationError
from kadi.lib.forms import JSONField
from kadi.lib.schemas import BaseSchema
from kadi.lib.schemas import CustomString
from kadi.lib.schemas import validate_iri as validate_iri_schema
from kadi.lib.utils import is_special_float
from kadi.lib.validation import validate_iri


class ExtrasJSONB(db.TypeDecorator):
    """Custom JSON type for values (potentially) containing extra metadata.

    Converts float values to float explicitly, as larger float values might otherwise be
    interpreted as integers. This also works with dictionaries that do not contain
    extras directly, but as any nested dictionary value instead. See also
    :attr:`.Record.extras`.
    """

    impl = JSONB

    cache_ok = True

    def _is_extra(self, value):
        # Extras always include a type and value, so this should be good enough to
        # detect them, as long as we don't have to deal with arbitrary JSON data.
        if isinstance(value, dict) and "type" in value and "value" in value:
            return True

        return False

    def process_result_value(self, value, dialect):
        """Convert float values of any extras recursively."""
        if value is None:
            return value

        if isinstance(value, dict):
            for val in value.values():
                self.process_result_value(val, dialect)

        elif isinstance(value, list) and len(value) > 0 and self._is_extra(value[0]):
            for extra in value:
                if is_nested_type(extra["type"]):
                    self.process_result_value(extra["value"], dialect)

                elif extra["type"] == "float" and extra["value"] is not None:
                    extra["value"] = float(extra["value"])

        return value


def _validate_extra_value(value, value_type):
    type_name = type(value).__name__

    if value_type == "int":
        if type_name == value_type:
            if const.EXTRAS_MIN_INTEGER <= value <= const.EXTRAS_MAX_INTEGER:
                return value

            raise KadiValidationError(
                _(
                    "Integer values must be between %(min)s and %(max)s.",
                    min=const.EXTRAS_MIN_INTEGER,
                    max=const.EXTRAS_MAX_INTEGER,
                )
            )

    elif value_type == "float":
        # Allow integer values as well.
        if type_name in {"int", "float"}:
            value = float(value)

            if not is_special_float(value):
                return value

    elif value_type == "date":
        # Allow using datetime objects directly as well.
        if not isinstance(value, datetime):
            value = parse_datetime_string(value)

        if value is not None:
            return value.astimezone(timezone.utc).isoformat()

    elif type_name == value_type:
        return value

    raise KadiValidationError(
        _("Not a valid %(type)s.", type=pretty_type_name(value_type))
    )


# Titles for all validation schema fields, translated in case the schema is used in the
# context of the corresponding form field.
VALIDATION_SCHEMA_FIELD_NAMES = {
    "required": _l("Required"),
    "range": _l("Range"),
    "options": _l("Options"),
    "iri": "IRI",
}


class _RangeSchema(BaseSchema):
    """Schema to represent number ranges in the validation instructions of extras."""

    min = fields.Raw(load_default=None)

    max = fields.Raw(load_default=None)


class _ValidationSchema(BaseSchema):
    """Schema to represent the validation instructions of extras."""

    required = fields.Boolean()

    range = fields.Nested(_RangeSchema)

    options = fields.List(fields.Raw)

    iri = fields.Boolean()

    def __init__(self, value_type, **kwargs):
        super().__init__(**kwargs)
        self.value_type = value_type

    def _flatten_errors(self, errors):
        # Flattening the error messages makes working with them easier, as we can then
        # always expect them to be a flat list of strings for each extra.
        flattened_messages = []

        for field_name, error_data in errors.items():
            field_name = VALIDATION_SCHEMA_FIELD_NAMES.get(field_name, field_name)

            if isinstance(error_data, dict):
                for messages in error_data.values():
                    for message in messages:
                        flattened_messages.append(f"{field_name}: {message}")
            else:
                for message in error_data:
                    flattened_messages.append(f"{field_name}: {message}")

        return flattened_messages

    def _check_type_compatibility(self, field, valid_types):
        if self.value_type not in valid_types:
            raise ValidationError(
                _(
                    "Cannot be used together with %(type)s.",
                    type=pretty_type_name(self.value_type),
                ),
                field,
            )

    @post_load
    def _post_load(self, data, **kwargs):
        if "required" in data and data["required"] is False:
            del data["required"]

        if (
            "range" in data
            and data["range"].get("min") is None
            and data["range"].get("max") is None
        ):
            del data["range"]

        if "options" in data and not data["options"]:
            del data["options"]

        if "iri" in data and data["iri"] is False:
            del data["iri"]

        return data

    @validates_schema(skip_on_field_errors=False)
    def _validate_schema(self, data, **kwargs):
        if "range" in data:
            self._check_type_compatibility("range", ["int", "float"])

            for key, value in data["range"].items():
                if value is not None:
                    try:
                        data["range"][key] = _validate_extra_value(
                            value, self.value_type
                        )
                    except KadiValidationError as e:
                        raise ValidationError(str(e), "range") from e

            min_value = data["range"]["min"]
            max_value = data["range"]["max"]

            if (
                min_value is not None
                and max_value is not None
                and min_value > max_value
            ):
                raise ValidationError(
                    _("Minimum value cannot be greater than maximum value."), "range"
                )

        if "options" in data:
            self._check_type_compatibility("options", ["str", "int", "float"])

            options = []

            for option in data["options"]:
                try:
                    _option = _validate_extra_value(option, self.value_type)

                    if data.get("iri", False):
                        validate_iri(_option)

                    if _option not in options:
                        options.append(_option)

                except KadiValidationError as e:
                    raise ValidationError(str(e), "options") from e

            data["options"] = options

        if "iri" in data:
            self._check_type_compatibility("iri", ["str"])


class ExtraSchema(BaseSchema):
    """Schema to represent extra metadata.

    Also does all necessary conversion and validation when deserializing. See also
    :attr:`.Record.extras`.

    :param is_template: (optional) Flag indicating whether the schema is used within the
        context a template, in which case slightly different validation rules apply.
    """

    type = CustomString(required=True, filter=strip)

    key = CustomString(required=True, filter=normalize)

    value = fields.Raw(load_default=None)

    unit = CustomString(filter=normalize, load_default=None)

    description = CustomString(filter=strip)

    term = CustomString(filter=strip, validate=validate_iri_schema)

    validation = fields.Dict()

    def __init__(self, is_template=False, **kwargs):
        super().__init__(**kwargs)
        self.is_template = is_template

    def _add_validation_error(self, errors, index, field, message):
        if self.many:
            if index not in errors:
                errors[index] = {field: [message]}
            elif field not in errors[index]:
                errors[index][field] = [message]
            else:
                errors[index][field].append(message)
        else:
            if field not in errors:
                errors[field] = [message]
            else:
                errors[field].append(message)

    def _apply_validation(self, extra, errors, index):
        add_validation_error = partial(
            self._add_validation_error, errors, index, "value"
        )

        value = extra["value"]
        validation = extra["validation"]

        # Handle the "required" validation.
        if validation.get("required", False) and not self.is_template and value is None:
            add_validation_error(_("Value is required."))

        # Handle the "range" validation.
        if "range" in validation and value is not None:
            min_value = validation["range"]["min"]

            if min_value is not None and value < min_value:
                add_validation_error(
                    _("Must be equal to or greater than %(min)s.", min=min_value),
                )

            max_value = validation["range"]["max"]

            if max_value is not None and value > max_value:
                add_validation_error(
                    _("Must be equal to or smaller than %(max)s.", max=max_value),
                )

        # Handle the "options" validation.
        if (
            "options" in validation
            and value is not None
            and value not in validation["options"]
        ):
            add_validation_error(
                _(
                    "Must be one of: %(options)s.",
                    options=", ".join(str(v) for v in validation["options"]),
                ),
            )

        # Handle the "iri" validation.
        if validation.get("iri", False) and value is not None:
            try:
                validate_iri(value)
            except KadiValidationError as e:
                add_validation_error(str(e))

    @post_load
    def _post_load(self, data, **kwargs):
        if "unit" in data and data.get("type") not in {"int", "float"}:
            del data["unit"]

        if "validation" in data and not data["validation"]:
            del data["validation"]

        return data

    @validates_schema(pass_many=True, skip_on_field_errors=False)
    def _validate_schema(self, data, **kwargs):
        data = data if self.many else [data]

        # To collect all validation errors.
        errors = {}
        # To check for duplicate keys.
        prev_keys = set()

        for index, extra in enumerate(data):
            # When the extra is completely empty, the input type was invalid, so we skip
            # our custom validation.
            if not extra:
                continue

            add_validation_error = partial(self._add_validation_error, errors, index)

            # Strip string values and replace empty string values with None.
            if isinstance(extra.get("value"), str):
                extra["value"] = extra["value"].strip() or None

            value_type = extra.get("type")

            if value_type in {"str", "int", "float", "bool", "date", "dict", "list"}:
                if is_nested_type(value_type):
                    # Set the value to an empty list if it is not present or None.
                    if extra.get("value") is None:
                        extra["value"] = []

                    schema_args = {"is_template": self.is_template, "many": True}

                    if value_type == "list":
                        # List values should have no keys at all.
                        schema_args["exclude"] = ["key"]

                    schema = ExtraSchema(**schema_args)

                    try:
                        extra["value"] = schema.load(extra.get("value"))
                    except ValidationError as e:
                        if self.many:
                            errors[index] = {"value": e.messages}
                        else:
                            errors["value"] = e.messages

                    if "validation" in extra:
                        add_validation_error(
                            "validation",
                            _(
                                "Cannot be used together with %(type)s.",
                                type=pretty_type_name(value_type),
                            ),
                        )
                else:
                    if extra.get("value") is not None:
                        try:
                            extra["value"] = _validate_extra_value(
                                extra["value"], value_type
                            )
                        except KadiValidationError as e:
                            add_validation_error("value", str(e))

                    if "validation" in extra:
                        try:
                            schema = _ValidationSchema(value_type)
                            extra["validation"] = schema.load(extra["validation"])
                            self._apply_validation(extra, errors, index)

                        except ValidationError as e:
                            for message in schema._flatten_errors(e.messages):
                                add_validation_error("validation", message)

                if value_type not in {"int", "float"}:
                    if extra.get("unit") is not None:
                        add_validation_error(
                            "unit",
                            _(
                                "Cannot be used together with %(type)s.",
                                type=pretty_type_name(value_type),
                            ),
                        )
            else:
                add_validation_error("type", _("Invalid value."))

            key = extra.get("key")

            if key in prev_keys:
                add_validation_error("key", _("Duplicate value."))

            if key:
                prev_keys.add(key)

        if errors:
            raise ValidationError(errors)


# Translated and adapted validation messages that can realistically occur when using the
# extras schema as part of its corresponding form field.
EXTRAS_FIELD_VALIDATIONS = {
    "Field may not be null.": _l("Value is required."),
}


class ExtrasField(JSONField):
    """Custom convenience field to process and validate extra metadata.

    Uses :class:`ExtraSchema` for its validation.

    :param is_template: (optional) See :class:`ExtraSchema`.
    """

    def __init__(self, *args, is_template=False, **kwargs):
        self.is_template = is_template
        self._validation_errors = {}

        kwargs["default"] = []
        super().__init__(*args, **kwargs)

    def _extras_to_formdata(self, extras, errors):
        # Try to merge the given extras and validation errors into suitable form data,
        # as far as possible.
        formdata = []

        for index, extra in enumerate(extras):
            if not isinstance(extra, dict):
                continue

            extra_formdata = {
                "type": {"value": "str", "errors": []},
                "key": {"value": None, "errors": []},
                "value": {"value": None, "errors": []},
                "unit": {"value": None, "errors": []},
                "description": {"value": None, "errors": []},
                "term": {"value": None, "errors": []},
                "validation": {"value": None, "errors": []},
            }

            for key, value in extra_formdata.items():
                if key in extra:
                    value["value"] = deepcopy(extra[key])

            for key, value in errors.get(index, {}).items():
                # Check if we actually have a list of errors for the field itself or a
                # nested errors dictionary, which will get handled via the recursion
                # (except for top level "_schema" errors, which we can ignore).
                if isinstance(value, list) and key in extra_formdata:
                    for error in value:
                        error = EXTRAS_FIELD_VALIDATIONS.get(error, error)
                        extra_formdata[key]["errors"].append(error)

            if is_nested_type(extra.get("type")) and isinstance(
                extra.get("value"), list
            ):
                extra_formdata["value"]["value"] = self._extras_to_formdata(
                    extra["value"], errors.get(index, {}).get("value", {})
                )

            formdata.append(extra_formdata)

        return formdata

    def _value(self):
        # Always try to use the raw form data first, if applicable.
        if self.raw_data:
            # Verify the basic structure of the raw data again.
            try:
                extras = json.loads(self.raw_data[0])
            except Exception as e:
                current_app.logger.debug(e, exc_info=True)
                return []

            if not isinstance(extras, list):
                return []

            return self._extras_to_formdata(extras, self._validation_errors)

        # Otherwise, use the data that was directly supplied, if applicable.
        if self.data:
            return self._extras_to_formdata(self.data, {})

        return []

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)

        if valuelist:
            try:
                schema = ExtraSchema(is_template=self.is_template, many=True)
                self.data = schema.load(self.data)

            except ValidationError as e:
                self._validation_errors = e.messages
                self.data = self.default
                raise ValueError("Invalid data structure.") from e


def is_nested_type(value_type):
    """Check if the type of an extra metadata entry is nested.

    :param value_type: The type of the extra metadata entry.
    :return: ``True`` if the given type is nested, ``False`` otherwise.
    """
    return value_type in {"dict", "list"}


def pretty_type_name(value_type):
    """Return a pretty type name based on the type of an extra metadata.

    :param value_type: The type of the extra metadata entry.
    :return: The pretty type name as string.
    """
    if value_type == "str":
        return "string"
    if value_type == "int":
        return "integer"
    if value_type == "bool":
        return "boolean"
    if value_type == "dict":
        return "dictionary"

    return value_type


def filter_extras(extras, excluded_extras):
    """Filter the given extra metadata.

    :param extras: The extras to filter
    :param excluded_extras: A filter mask of extra metadata keys to exclude. See
        :func:`get_record_export_data`.
    :return: A copy of the filtered extras.
    """
    filtered_extras = []

    if not isinstance(excluded_extras, dict):
        excluded_extras = {}

    for index, extra in enumerate(extras):
        filter_key = extra.get("key", str(index))

        # If the dictionary corresponding to the key is empty, the whole extra is
        # excluded.
        if (
            filter_key in excluded_extras
            and isinstance(excluded_extras[filter_key], dict)
            and len(excluded_extras[filter_key]) == 0
        ):
            continue

        new_extra = deepcopy(extra)

        if is_nested_type(extra["type"]):
            new_extra["value"] = filter_extras(
                extra["value"], excluded_extras.get(filter_key)
            )

        filtered_extras.append(new_extra)

    return filtered_extras


def remove_extra_values(extras):
    """Remove all values of the the given extra metadata.

    :param extras: The extras for which the values are to be removed.
    :return: A copy of the extras without values.
    """
    new_extras = []

    for extra in extras:
        new_extra = deepcopy(extra)

        if is_nested_type(extra["type"]):
            new_extra["value"] = remove_extra_values(extra["value"])
        else:
            new_extra["value"] = None

        new_extras.append(new_extra)

    return new_extras


def _extras_to_plain_json(extras, nested_type=None):
    if nested_type == "list":
        converted_extras = []
    else:
        converted_extras = {}

    for extra in extras:
        if is_nested_type(extra["type"]):
            value = _extras_to_plain_json(extra["value"], nested_type=extra["type"])
        else:
            value = extra["value"]

        if nested_type == "list":
            converted_extras.append(value)
        else:
            converted_extras[extra["key"]] = value

    return converted_extras


def extras_to_plain_json(extras):
    """Convert the given extra metadata to a plain JSON structure.

    :param extras: The extras to convert.
    :return: The converted extras as dictionary.
    """
    return _extras_to_plain_json(extras)
