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
from flask import abort
from flask import request
from flask_babel import gettext as _
from marshmallow import EXCLUDE
from marshmallow import Schema
from marshmallow import ValidationError
from marshmallow import fields

from kadi.lib.api.core import json_error_response
from kadi.lib.api.utils import is_internal_api_request
from kadi.lib.utils import as_list
from kadi.lib.validation import validate_mimetype as _validate_mimetype

from .validation import validate_identifier as _validate_identifier
from .validation import validate_iri as _validate_iri
from .validation import validate_uuid
from .validation import validator


class BaseSchema(Schema):
    """Base class for all schemas.

    Note that all schemas that inherit from this class will silently exclude unknown
    fields by default.

    :param _internal: (optional) Flag indicating whether additional data that's only
        relevant for internal use should be included when serializing objects. If not
        set, the value returned by :func:`kadi.lib.api.utils.is_internal_api_request`
        will be taken instead. Note that this flag will generally not be passed
        automatically to any nested schemas.
    """

    class Meta:
        """Container to store meta class attributes."""

        unknown = EXCLUDE

    def __init__(self, *args, _internal=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._internal = _internal

        if self._internal is None:
            self._internal = is_internal_api_request()

    def load_or_400(self, data=None):
        """Try to deserialize the given input.

        Will try to deserialize/load the given input data using the schemas ``load``
        method. If the validation fails or if the input is no valid JSON data in the
        first place, automatically abort the current request with status code 400 and a
        corresponding error response as JSON.

        :param data: (optional) The input to deserialize. Defaults to the JSON body of
            the current request.
        :return: The deserialized input.
        """
        try:
            # Always try to parse the data, even if no correct "Content-Type" header is
            # set, which makes handling JSON data more consistent with other content
            # types.
            data = data if data is not None else request.get_json(force=True)
        except:
            abort(json_error_response(400, description="Failed to decode JSON object."))

        try:
            data = self.load(data)
        except ValidationError as e:
            abort(json_error_response(400, errors=e.messages))

        return data


class CustomString(fields.String):
    """Custom string field that implements additional filtering and validation.

    :param allow_ws_only: (optional) Flag indicating whether strings that are empty or
        only contain whitespace will be considered valid.
    :param filter: (optional) A single or a list of filter and/or conversion functions
        that will be applied when deserializing the field data.
    """

    def __init__(self, *args, allow_ws_only=False, filter=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.allow_ws_only = allow_ws_only
        self.filter = as_list(filter if filter is not None else [])

    def _deserialize(self, value, attr, data, **kwargs):
        output = super()._deserialize(value, attr, data, **kwargs)

        if not self.allow_ws_only and not output.strip():
            raise ValidationError(_("String must not be empty."))

        for _filter in self.filter:
            output = _filter(output)

        return output


class CustomPluck(fields.Pluck):
    """Custom pluck field that implements additional (de)serialization options.

    :param sort: (optional) Flag indicating whether serialized and deserialized output
        should be sorted if ``many`` is set.
    :param flatten: (optional) Flag indicating whether deserialized output should be
        flattened, i.e. extracted from its outer dictionary. The same logic will also be
        applied to potential validation errors.
    :param unique: (optional) Flag indicating whether deserialized items should be
        unique if ``many`` is set.
    """

    def __init__(self, *args, sort=True, flatten=True, unique=True, **kwargs):
        super().__init__(*args, **kwargs)

        self.sort = sort
        self.flatten = flatten
        self.unique = unique

    def _serialize(self, *args, **kwargs):
        output = super()._serialize(*args, **kwargs)

        if self.many and self.sort:
            return sorted(output)

        return output

    def _deserialize(self, *args, **kwargs):
        try:
            output = super()._deserialize(*args, **kwargs)
        except ValidationError as e:
            if not self.flatten or not isinstance(e.messages, dict):
                raise

            if self.many:
                for index, error_data in e.messages.items():
                    if isinstance(error_data, dict):
                        e.messages[index] = error_data[self.field_name]
            else:
                e.messages = e.messages[self.field_name]

            raise ValidationError(e.messages) from e

        if self.many:
            if self.unique:
                unique_output = []
                prev_values = set()

                for item in output:
                    value = item[self.field_name]

                    if value not in prev_values:
                        unique_output.append(item)
                        prev_values.add(value)

                output = unique_output

            if self.sort:
                output = sorted(output, key=lambda item: item[self.field_name])

            if self.flatten:
                return [item[self.field_name] for item in output]

        elif self.flatten:
            return output[self.field_name]

        return output


class ValidateUUID:
    """Validate a UUID of a specific version in a schema field.

    :param version: (optional) The UUID version.
    """

    def __init__(self, version=4):
        self.version = version

    @validator(ValidationError)
    def __call__(self, value):
        validate_uuid(value, version=self.version)


@validator(ValidationError)
def validate_identifier(value):
    """Validate an identifier in a schema field.

    Uses :func:`kadi.lib.validation.validate_identifier`.

    :param value: The field value.
    """
    _validate_identifier(value)


@validator(ValidationError)
def validate_mimetype(value):
    """Validate a MIME type in a schema field.

    Uses :func:`kadi.lib.validation.validate_mimetype`.

    :param value: The field value.
    """
    _validate_mimetype(value)


@validator(ValidationError)
def validate_iri(value):
    """Validate an IRI in a schema field.

    Uses :func:`kadi.lib.validation.validate_iri`.

    :param value: The field value.
    """
    _validate_iri(value)
