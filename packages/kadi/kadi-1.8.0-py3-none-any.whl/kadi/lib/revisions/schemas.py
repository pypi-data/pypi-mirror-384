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
from uuid import UUID

from marshmallow import fields
from marshmallow import post_dump

from kadi.lib.api.core import check_access_token_scopes
from kadi.lib.schemas import BaseSchema
from kadi.lib.web import url_for
from kadi.modules.accounts.schemas import UserSchema

from .utils import get_revision_columns


class ObjectRevisionSchema(BaseSchema):
    """Schema to represent object revisions.

    :param schema: The schema to represent the object revisions with.
    :param compared_revision: (optional) Another revision object to compare the object
        revisions with. By default, the comparison always uses the previous object
        revision, if applicable.
    :param api_endpoint: (optional) An API endpoint to retrieve the current object
        revision.
    :param view_endpoint: (optional) An endpoint to view the current object revision.
        Only relevant for internal use.
    :param endpoint_args: (optional) Additional keyword arguments to append to the API
        and/or view endpoints when building the corresponding URL.
    :param view_object_url: (optional) A URL to view the actual object the current
        revision refers to. Only relevant for internal use.
    """

    id = fields.Integer(dump_only=True)

    timestamp = fields.DateTime(dump_only=True)

    user = fields.Nested(UserSchema, dump_only=True)

    object_id = fields.Method("_generate_object_id")

    data = fields.Method("_generate_data")

    diff = fields.Method("_generate_diff")

    _links = fields.Method("_generate_links")

    def __init__(
        self,
        schema,
        compared_revision=None,
        api_endpoint=None,
        view_endpoint=None,
        endpoint_args=None,
        view_object_url=None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.schema = schema
        self.compared_revision = compared_revision
        self.api_endpoint = api_endpoint
        self.view_endpoint = view_endpoint
        self.endpoint_args = endpoint_args if endpoint_args is not None else {}
        self.view_object_url = view_object_url

    @post_dump
    def _post_dump(self, data, **kwargs):
        if "user" in data and not check_access_token_scopes("user.read"):
            del data["user"]

        if "_links" in data and not data["_links"]:
            del data["_links"]

        return data

    def _generate_object_id(self, obj):
        object_id = getattr(obj, f"{obj.model_class.__tablename__}_id")
        return str(object_id) if isinstance(object_id, UUID) else object_id

    def _generate_data(self, obj):
        cols, rels = get_revision_columns(obj.model_class)
        schema = self.schema(only=cols + [rel[0] for rel in rels])

        return schema.dump(obj)

    def _generate_diff(self, obj):
        cols, rels = get_revision_columns(obj.model_class)
        schema = self.schema(only=cols + [rel[0] for rel in rels])

        revision_data = schema.dump(obj)

        compared_revision = (
            self.compared_revision if self.compared_revision is not None else obj.parent
        )
        compared_data = (
            schema.dump(compared_revision) if compared_revision is not None else {}
        )

        diff = {}

        for key, value in revision_data.items():
            compared_value = compared_data.get(key)

            # A simple comparison should be sufficient after the deserialization.
            if value != compared_value:
                diff[key] = compared_value

        return diff

    def _generate_links(self, obj):
        links = {}

        if self.api_endpoint:
            links["self"] = url_for(
                self.api_endpoint, revision_id=obj.id, **self.endpoint_args
            )

            if obj.parent:
                links["parent"] = url_for(
                    self.api_endpoint, revision_id=obj.parent.id, **self.endpoint_args
                )

            if obj.child:
                links["child"] = url_for(
                    self.api_endpoint, revision_id=obj.child.id, **self.endpoint_args
                )

        if self._internal:
            if self.view_endpoint:
                links["view"] = url_for(
                    self.view_endpoint, revision_id=obj.id, **self.endpoint_args
                )

            if self.view_object_url:
                links["view_object"] = self.view_object_url

        return links
