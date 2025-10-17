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

from flask import json
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask_wtf.i18n import translations as wtf_translations
from markupsafe import escape
from werkzeug.datastructures import FileStorage
from wtforms import BooleanField as _BooleanField
from wtforms import DateTimeField
from wtforms import Field
from wtforms import FileField as _FileField
from wtforms import IntegerField as _IntegerField
from wtforms import PasswordField as _PasswordField
from wtforms import SelectField as _SelectField
from wtforms import SelectMultipleField
from wtforms import StringField as _StringField
from wtforms import SubmitField as _SubmitField
from wtforms import TextAreaField
from wtforms.validators import Length
from wtforms.validators import StopValidation

from kadi.lib.config.core import MISSING
from kadi.lib.config.core import get_sys_config
from kadi.lib.config.core import set_sys_config
from kadi.lib.utils import compact_json

from .validation import validate_identifier as _validate_identifier
from .validation import validate_iri as _validate_iri
from .validation import validate_mimetype as _validate_mimetype
from .validation import validate_username as _validate_username
from .validation import validator


SCHEMA_FORM_ERRORS = {
    "Field may not be null.": "This field is required.",
}


class CustomFieldMixin:
    """Mixin class for all custom fields and for wrapping existing fields.

    Adds a common dictionary conversion to all inheriting fields and also handles some
    common corner cases.
    """

    def __call__(self):
        """Convert this field into a JSON representation for use in HTML templates.

        :return: An escaped markup object representing the dictionary returned by
            :meth:`to_dict` serialized as JSON.
        """
        return escape(compact_json(self.to_dict(), ensure_ascii=True, sort_keys=False))

    def process_formdata(self, valuelist):
        # pylint: disable=missing-function-docstring
        if valuelist:
            # The file should always be listed first.
            value = valuelist[0]

            is_file = isinstance(value, FileStorage)
            is_file_field = isinstance(self, FileField)

            # Workaround to handle corner cases where a file is expected but a string is
            # supplied and vice versa.
            if is_file != is_file_field:
                raise ValueError("Incorrect value format.")

        super().process_formdata(valuelist)

    def to_dict(self):
        """Convert this field into a dictionary representation."""
        data = {
            "id": self.id,
            "name": self.name,
            "label": str(self.label.text),
            "description": str(self.description),
            "errors": self.errors or [],
            "data": self.data if self.data is not None else "",
            "validation": {
                "required": self.flags.required or False,
            },
        }

        for validator in self.validators:
            if isinstance(validator, Length):
                if validator.min != -1:
                    data["validation"]["min"] = validator.min

                if validator.max != -1:
                    data["validation"]["max"] = validator.max

        return data


class BooleanField(CustomFieldMixin, _BooleanField):
    """Regular boolean field inheriting from :class:`CustomFieldMixin`."""


class IntegerField(CustomFieldMixin, _IntegerField):
    """Regular integer field inheriting from :class:`CustomFieldMixin`."""


class StringField(CustomFieldMixin, _StringField):
    """Regular string field inheriting from :class:`CustomFieldMixin`."""


class SubmitField(CustomFieldMixin, _SubmitField):
    """Regular submit field inheriting from :class:`CustomFieldMixin`."""


class PasswordField(CustomFieldMixin, _PasswordField):
    """Regular password field inheriting from :class:`CustomFieldMixin`."""

    def to_dict(self):
        data = super().to_dict()

        data["data"] = ""
        return data


class FileField(CustomFieldMixin, _FileField):
    """Custom file field."""

    def to_dict(self):
        data = super().to_dict()

        data["data"] = None
        return data


class LFTextAreaField(CustomFieldMixin, TextAreaField):
    """Custom text area field that converts *CRLF* to *LF*."""

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)

        if valuelist:
            self.data = self.data.replace("\r\n", "\n")


class UTCDateTimeField(CustomFieldMixin, DateTimeField):
    """Custom timezone aware DateTimeField using UTC.

    :param date_format: (optional) The date format to use for parsing and serializing.
    """

    def __init__(self, *args, date_format="%Y-%m-%dT%H:%M:%S.%fZ", **kwargs):
        kwargs["format"] = date_format
        super().__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)

        if valuelist:
            self.data = self.data.replace(tzinfo=timezone.utc)

    def to_dict(self):
        data = super().to_dict()

        data["data"] = self._value()
        return data


class SelectField(CustomFieldMixin, _SelectField):
    """Custom select field."""

    def to_dict(self):
        data = super().to_dict()

        if self.choices is not None:
            data["choices"] = [(val, str(title)) for val, title in self.choices]
        else:
            data["choices"] = []

        return data


class DynamicSelectField(CustomFieldMixin, _SelectField):
    """Custom select field for dynamically generated selections.

    Note that this field automatically replaces empty strings in the form data with its
    default value (``None``) instead of trying to coerce them.

    In addition, the instance variable ``initial`` can be used to specify an initial
    value to prefill the selection with by setting it to a tuple containing the actual
    value and a corresponding text to be displayed within the selection.
    """

    def __init__(self, *args, **kwargs):
        self.initial = None

        kwargs["default"] = None
        kwargs["choices"] = []
        kwargs["validate_choice"] = False

        super().__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            value = valuelist[0].strip()

            if not value:
                self.data = self.default
            else:
                super().process_formdata(valuelist)

    def to_dict(self):
        data = super().to_dict()

        data["data"] = self.initial
        return data


class DynamicMultiSelectField(CustomFieldMixin, SelectMultipleField):
    """Custom multi select field for dynamically generated selections.

    The instance variable ``initial`` can be used to set a list of initial values to
    prefill the selection with. See also :class:`DynamicSelectField`.
    """

    def __init__(self, *args, **kwargs):
        self.initial = []

        kwargs["default"] = []
        kwargs["choices"] = []
        kwargs["validate_choice"] = False

        super().__init__(*args, **kwargs)

    def to_dict(self):
        data = super().to_dict()

        data["data"] = self.initial
        return data


class JSONField(CustomFieldMixin, Field):
    """Custom field that processes its data as JSON."""

    def _value(self):
        return self.data

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)

        if valuelist:
            try:
                self.data = json.loads(self.data)
            except Exception as e:
                self.data = self.default
                raise ValueError(_("Invalid JSON data.")) from e

    def to_dict(self):
        data = super().to_dict()

        data["data"] = self._value()
        return data


class BaseForm(FlaskForm):
    """Base class for all forms.

    :param suffix: (optional) A suffix that will be appended to all field IDs in the
        form of ``"<id>_<suffix>"``. This is especially useful when dealing with
        multiple forms on the same page. Note that this differs in behavior from the
        ``prefix`` parameter of WTForms, since only the IDs of fields are effected and
        not their names.
    """

    def __init__(self, *args, suffix=None, **kwargs):
        super().__init__(*args, **kwargs)

        if suffix is not None:
            for field in self._fields.values():
                field.id = field.label.field_id = f"{field.id}_{suffix}"


class BaseConfigForm(BaseForm):
    r"""Base form class for use in setting config items.

    All fields in an inheriting form will be populated automatically from suitable
    config items stored in the database, if applicable. As keys for the config items,
    the field names are taken in uppercase.

    :param user: (optional) A user indicating whether global or user-specific config
        items are to be used for prepopulating the form and when setting the values of
        config items in the database via :meth:`set_config_values`.
    :param key_prefix: (optional) A string value to use as a prefix for all config items
        retrieved from and saved in the database. The prefix is used in uppercase and
        combined with each uppercase field name in the form of
        ``"<key_prefix>_<field_name>"``.
    :param ignored_fields: (optional) A set of field names, as specified in the class
        attributes, to ignore when prepopulating the form and when setting the values of
        config items in the database via :meth:`set_config_values`. Note that the
        ``"submit"`` field is always ignored.
    :param encrypted_fields: (optional) A set of field names, as specified in the class
        attributes, to use encryption/decryption for when prepopulating the form and
        when setting the values of config items in the database via
        :meth:`set_config_values`. Note that this only works for user-specific config
        items.
    :param \**kwargs: Additional keyword arguments to pass to :class:`.BaseForm`.
    """

    submit = SubmitField(_l("Save changes"))

    def _iterate_fields(self, callback):
        for field in self._unbound_fields:
            field_name = field[0]

            if field_name not in self._ignored_fields:
                callback(field_name)

    def __init__(
        self,
        *args,
        user=None,
        key_prefix=None,
        ignored_fields=None,
        encrypted_fields=None,
        **kwargs,
    ):
        self._user = user
        self._key_prefix = f"{key_prefix.upper()}_" if key_prefix else ""
        self._ignored_fields = ignored_fields if ignored_fields is not None else set()
        self._ignored_fields.add("submit")
        self._encrypted_fields = (
            encrypted_fields if encrypted_fields is not None else set()
        )

        kwargs["data"] = {}

        def _prepopulate_fields(field_name):
            config_key = self._key_prefix + field_name.upper()

            if self._user is None:
                config_value = get_sys_config(config_key, use_fallback=False)
            else:
                config_value = self._user.get_config(
                    config_key, decrypt=field_name in self._encrypted_fields
                )

            if config_value is not MISSING:
                kwargs["data"][field_name] = config_value

        self._iterate_fields(_prepopulate_fields)

        super().__init__(*args, **kwargs)

    def set_config_values(self):
        """Automatically set all config items based on the respective field data.

        Useful to populate all relevant config items in the database after a form is
        submitted. Similar to prepopulating the form fields, the names of the fields are
        taken in uppercase as keys for each config item.
        """

        def _set_config_value(field_name):
            config_key = self._key_prefix + field_name.upper()
            field_data = getattr(self, field_name).data

            if self._user is None:
                set_sys_config(config_key, field_data)
            else:
                self._user.set_config(
                    config_key, field_data, encrypt=field_name in self._encrypted_fields
                )

        self._iterate_fields(_set_config_value)


@validator(StopValidation)
def validate_identifier(form, field):
    """Validate an identifier in a form field.

    Uses :func:`kadi.lib.validation.validate_identifier`.

    :param form: The form object.
    :param field: The field object.
    """
    if field.data is not None:
        _validate_identifier(field.data)


@validator(StopValidation)
def validate_mimetype(form, field):
    """Validate a MIME type in a form field.

    Uses :func:`kadi.lib.validation.validate_mimetype`.

    :param form: The form object.
    :param field: The field object.
    """
    if field.data is not None:
        _validate_mimetype(field.data)


@validator(StopValidation)
def validate_username(form, field):
    """Validate a local username in a form field.

    Uses :func:`kadi.lib.validation.validate_username`.

    :param form: The form object.
    :param field: The field object.
    """
    if field.data is not None:
        _validate_username(field.data)


@validator(StopValidation)
def validate_iri(form, field):
    """Validate an IRI in a form field.

    Uses :func:`kadi.lib.validation.validate_iri`.

    :param form: The form object.
    :param field: The field object.
    """
    if field.data is not None:
        _validate_iri(field.data)


def convert_schema_validation_msg(msg, **interpolations):
    r"""Convert a schema validation message to a corresponding form field message.

    This is mainly useful when using a schema for validation in a field in order to
    better match the usual form validation messages. Note that, if possible, the
    messages will be translated using the translations provided by WTForms.

    :param msg: The validation message to convert.
    :param \**interpolations: Additional keyword arguments to provide interpolation
        values for the converted validation message.
    :return: The converted validation message or the original message if it could not be
        converted.
    """

    # Avoids the strings from being extracted, as we don't want to translate them
    # ourselves.
    ngettext_func = wtf_translations.ngettext

    if msg.startswith("Longer than maximum length"):
        max_value = interpolations.get("max", -1)
        msg = ngettext_func(
            "Field cannot be longer than %(max)d character.",
            "Field cannot be longer than %(max)d characters.",
            max_value,
        )
        return msg % {"max": max_value}

    msg = SCHEMA_FORM_ERRORS.get(msg, msg)
    return wtf_translations.gettext(msg)
