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
from marshmallow import fields

from kadi.lib.conversion import lower
from kadi.lib.conversion import strip
from kadi.lib.schemas import BaseSchema
from kadi.lib.schemas import CustomString
from kadi.lib.web import url_for


class RoleSchema(BaseSchema):
    """Schema to represent roles.

    See :class:`.Role`.
    """

    name = CustomString(required=True, filter=[lower, strip])


class RoleRuleSchema(BaseSchema):
    """Schema to represent role rules.

    See :class:`.RoleRule`.
    """

    id = fields.Integer(dump_only=True)

    type = fields.String(dump_only=True)

    condition = fields.Raw(dump_only=True)

    role = fields.Nested(RoleSchema, dump_only=True)

    created_at = fields.DateTime(dump_only=True)

    _actions = fields.Method("_generate_actions")

    def _generate_actions(self, obj):
        return {
            "remove": url_for(
                f"api.remove_{obj.role.object}_role_rule",
                rule_id=obj.id,
                **{f"{obj.role.object}_id": obj.role.object_id},
            )
        }
