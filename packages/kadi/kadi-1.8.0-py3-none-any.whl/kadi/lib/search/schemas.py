# Copyright 2023 Karlsruhe Institute of Technology
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
from marshmallow.validate import Length
from marshmallow.validate import OneOf

import kadi.lib.constants as const
from kadi.lib.conversion import normalize
from kadi.lib.conversion import strip
from kadi.lib.schemas import BaseSchema
from kadi.lib.schemas import CustomString
from kadi.lib.web import url_for

from .models import SavedSearch


class SavedSearchSchema(BaseSchema):
    """Schema to represent saved searches.

    See :class:`.SavedSearch`.
    """

    id = fields.Integer(dump_only=True)

    name = CustomString(
        required=True,
        filter=normalize,
        validate=Length(
            max=SavedSearch.Meta.check_constraints["name"]["length"]["max"]
        ),
    )

    object = CustomString(required=True, validate=OneOf(list(const.RESOURCE_TYPES)))

    query_string = CustomString(
        required=True,
        allow_ws_only=True,
        filter=strip,
        validate=Length(
            max=SavedSearch.Meta.check_constraints["query_string"]["length"]["max"]
        ),
    )

    _actions = fields.Method("_generate_actions")

    _links = fields.Method("_generate_links")

    def _generate_actions(self, obj):
        return {
            "edit": url_for("api.edit_saved_search", id=obj.id),
            "remove": url_for("api.remove_saved_search", id=obj.id),
        }

    def _generate_links(self, obj):
        links = {"self": url_for("api.get_saved_search", id=obj.id)}

        if self._internal and obj.object in const.RESOURCE_TYPES:
            links["view"] = url_for(
                const.RESOURCE_TYPES[obj.object]["endpoint"],
                **{**obj.qparams, "saved_search": obj.id},
            )

        return links
