# Copyright 2024 Karlsruhe Institute of Technology
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
from marshmallow import post_dump

import kadi.lib.constants as const
from kadi.lib.schemas import BaseSchema
from kadi.lib.web import url_for


class BasicResourceSchema(BaseSchema):
    """Schema to represent the basic attributes and different types of resources.

    These resources may refer to instances of :class:`.Record`, :class:`.Collection`,
    :class:`.Template` or :class:`.Group`.
    """

    id = fields.Integer(dump_only=True)

    title = fields.String(dump_only=True)

    identifier = fields.String(dump_only=True)

    visibility = fields.String(dump_only=True)

    created_at = fields.DateTime(dump_only=True)

    last_modified = fields.DateTime(dump_only=True)

    type = fields.String(dump_only=True)

    pretty_type = fields.Method("_get_pretty_type")

    _links = fields.Method("_generate_links")

    @post_dump
    def _post_dump(self, data, **kwargs):
        if "pretty_type" in data and data["pretty_type"] is None:
            del data["pretty_type"]

        if "_links" in data and not data["_links"]:
            del data["_links"]

        return data

    def _get_pretty_type(self, obj):
        if self._internal:
            return const.RESOURCE_TYPES[obj.type]["title"]

        return None

    def _generate_links(self, obj):
        links = {}

        if self._internal:
            links["view"] = url_for(f"{obj.type}s.view_{obj.type}", id=obj.id)

        return links


class DeletedResourceSchema(BasicResourceSchema):
    """Schema to represent the basic attributes of deleted resources."""

    # We simply reuse the last modification date, as it should not change anymore for
    # deleted resources even when updating them.
    last_modified = fields.DateTime(dump_only=True, data_key="deleted_at")

    _actions = fields.Method("_generate_actions")

    def _generate_actions(self, obj):
        return {
            "restore": url_for(f"api.restore_{obj.type}", id=obj.id),
            "purge": url_for(f"api.purge_{obj.type}", id=obj.id),
        }
