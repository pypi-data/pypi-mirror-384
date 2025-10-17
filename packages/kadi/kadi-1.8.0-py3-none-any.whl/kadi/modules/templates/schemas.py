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
from marshmallow import ValidationError
from marshmallow import fields
from marshmallow import post_load
from marshmallow import validates
from marshmallow.validate import Length
from marshmallow.validate import OneOf
from marshmallow.validate import Range

import kadi.lib.constants as const
from kadi.lib.conversion import lower
from kadi.lib.conversion import normalize
from kadi.lib.conversion import strip
from kadi.lib.licenses.schemas import LicenseSchema
from kadi.lib.resources.schemas import BaseResourceSchema
from kadi.lib.resources.schemas import ResourceRoleDataSchema
from kadi.lib.resources.schemas import check_duplicate_identifier
from kadi.lib.schemas import BaseSchema
from kadi.lib.schemas import CustomPluck
from kadi.lib.schemas import CustomString
from kadi.lib.schemas import validate_identifier
from kadi.lib.tags.schemas import TagSchema
from kadi.lib.web import url_for
from kadi.modules.records.extras import ExtraSchema
from kadi.modules.records.models import Record
from kadi.modules.records.schemas import RecordLinkDataSchema

from .models import Template
from .models import TemplateType


class RecordTemplateDataSchema(BaseSchema):
    """Schema to represent the data of record templates.

    See :attr:`.Template.data`.
    """

    identifier = CustomString(
        allow_ws_only=True,
        filter=[lower, strip],
        load_default="",
        validate=Length(max=const.RESOURCE_IDENTIFIER_MAX_LEN),
    )

    title = CustomString(
        allow_ws_only=True,
        filter=normalize,
        load_default="",
        validate=Length(max=const.RESOURCE_TITLE_MAX_LEN),
    )

    description = CustomString(
        allow_ws_only=True,
        filter=strip,
        load_default="",
        validate=Length(max=const.RESOURCE_DESCRIPTION_MAX_LEN),
    )

    type = CustomString(
        filter=[lower, normalize],
        load_default=None,
        validate=Length(max=Record.Meta.check_constraints["type"]["length"]["max"]),
    )

    license = CustomPluck(LicenseSchema, "name", load_default=None)

    extras = fields.Method(
        "_serialize_extras", deserialize="_deserialize_extras", load_default=lambda: []
    )

    tags = CustomPluck(TagSchema, "name", many=True, load_default=lambda: [])

    collections = fields.List(
        fields.Integer(validate=Range(min=1)), load_default=lambda: []
    )

    record_links = fields.Nested(
        RecordLinkDataSchema, many=True, load_default=lambda: []
    )

    roles = fields.Nested(
        ResourceRoleDataSchema(list(Record.Meta.permissions["roles"]), many=True),
        load_default=lambda: [],
    )

    @validates("identifier")
    def _validate_identifier(self, value):
        # Skip the format validation if the identifier value is empty.
        if value:
            validate_identifier(value)

    def _serialize_extras(self, obj):
        return obj.extras

    def _deserialize_extras(self, value):
        return ExtraSchema(is_template=True, many=True).load(value)


class TemplateSchema(BaseResourceSchema):
    """Schema to represent generic templates.

    See :class:`.Template`.

    :param previous_template: (optional) A template whose identifier should be excluded
        when checking for duplicates while deserializing.
    :param template_type: (optional) The type of the template. Used when deserializing
        the data and it contains no type value.
    """

    type = CustomString(
        required=True,
        filter=[lower, strip],
        validate=OneOf(Template.Meta.check_constraints["type"]["values"]),
    )

    data = fields.Raw(
        required=True,
        metadata={
            "type": {
                "oneOf": [
                    {"type": "object"},
                    {"type": "array", "items": {"type": "object"}},
                ]
            },
        },
    )

    _links = fields.Method("_generate_links")

    _actions = fields.Method("_generate_actions")

    def __init__(self, previous_template=None, template_type=None, **kwargs):
        super().__init__(**kwargs)

        self.previous_template = previous_template
        self.template_type = template_type

    @validates("id")
    def _validate_id(self, value):
        if Template.query.get_active(value) is None:
            raise ValidationError("No template with this ID exists.")

    @validates("identifier")
    def _validate_identifier(self, value):
        check_duplicate_identifier(Template, value, exclude=self.previous_template)

    @post_load
    def _post_load(self, data, **kwargs):
        if "data" not in data:
            return data

        current_type = data.get("type") or self.template_type

        if current_type == TemplateType.RECORD:
            schema = RecordTemplateDataSchema()
        elif current_type == TemplateType.EXTRAS:
            schema = ExtraSchema(is_template=True, many=True)
        else:
            # Will also be triggered when providing an invalid template type directly.
            raise ValidationError("Invalid value.", "type")

        try:
            data["data"] = schema.load(data["data"])
        except ValidationError as e:
            raise ValidationError(e.messages, "data") from e

        return data

    def _generate_links(self, obj):
        return {
            "self": url_for("api.get_template", id=obj.id),
            "user_roles": url_for("api.get_template_user_roles", id=obj.id),
            "group_roles": url_for("api.get_template_group_roles", id=obj.id),
            "revisions": url_for("api.get_template_revisions", id=obj.id),
            "view": url_for("templates.view_template", id=obj.id),
        }

    def _generate_actions(self, obj):
        return {
            "edit": url_for("api.edit_template", id=obj.id),
            "delete": url_for("api.delete_template", id=obj.id),
            "add_user_role": url_for("api.add_template_user_role", id=obj.id),
            "add_group_role": url_for("api.add_template_group_role", id=obj.id),
        }


class TemplateImportSchema(TemplateSchema):
    """Schema to represent imported template data."""

    @validates("id")
    def _validate_id(self, value):
        pass

    @validates("identifier")
    def _validate_identifier(self, value):
        pass
