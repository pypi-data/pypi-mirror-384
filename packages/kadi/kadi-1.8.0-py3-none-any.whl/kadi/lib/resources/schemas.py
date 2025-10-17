# Copyright 2022 Karlsruhe Institute of Technology
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
from marshmallow import post_dump
from marshmallow import validates
from marshmallow.validate import Length
from marshmallow.validate import OneOf
from marshmallow.validate import Range

import kadi.lib.constants as const
from kadi.lib.api.core import check_access_token_scopes
from kadi.lib.conversion import lower
from kadi.lib.conversion import normalize
from kadi.lib.conversion import strip
from kadi.lib.schemas import BaseSchema
from kadi.lib.schemas import CustomString
from kadi.lib.schemas import validate_identifier
from kadi.lib.web import url_for
from kadi.modules.groups.models import Group


class BaseResourceSchema(BaseSchema):
    """Base schema class to represent different kinds of resources.

    These resources may refer to instances of :class:`.Record`, :class:`.Collection`,
    :class:`.Template` or :class:`.Group`.
    """

    id = fields.Integer(required=True)

    identifier = CustomString(
        required=True,
        filter=[lower, strip],
        validate=[Length(max=const.RESOURCE_IDENTIFIER_MAX_LEN), validate_identifier],
    )

    title = CustomString(
        required=True,
        filter=normalize,
        validate=Length(max=const.RESOURCE_TITLE_MAX_LEN),
    )

    description = CustomString(
        allow_ws_only=True,
        filter=strip,
        validate=Length(max=const.RESOURCE_DESCRIPTION_MAX_LEN),
    )

    visibility = CustomString(
        filter=[lower, strip],
        validate=OneOf(
            [const.RESOURCE_VISIBILITY_PRIVATE, const.RESOURCE_VISIBILITY_PUBLIC]
        ),
    )

    plain_description = fields.String(dump_only=True)

    state = fields.String(dump_only=True)

    created_at = fields.DateTime(dump_only=True)

    last_modified = fields.DateTime(dump_only=True)

    creator = fields.Nested("UserSchema", dump_only=True)

    @post_dump
    def _post_dump(self, data, **kwargs):
        if "creator" in data and not check_access_token_scopes("user.read"):
            del data["creator"]

        return data


class BaseResourceRoleSchema(BaseSchema):
    """Base schema class to represent different kinds of resource roles.

    :param obj: (optional) An object that the current resource role refers to, which may
        be used when generating corresponding actions.
    """

    role = fields.Nested("RoleSchema", required=True)

    _actions = fields.Method("_generate_actions")

    def __init__(self, obj=None, **kwargs):
        super().__init__(**kwargs)
        self.obj = obj

    def _generate_actions(self, obj):
        return {}


class UserResourceRoleSchema(BaseResourceRoleSchema):
    """Schema to represent user roles.

    :param obj: (optional) An object that the current user role refers to. An instance
        of :class:`.Record`, :class:`.Collection`, :class:`.Template` or
        :class:`.Group`. See also :class:`BaseResourceRoleSchema`.
    """

    user = fields.Nested("UserSchema", required=True)

    def _generate_actions(self, obj):
        actions = {}

        try:
            user = getattr(obj, "user")
        except:
            user = obj.get("user")

        if user is None or self.obj is None:
            return actions

        if isinstance(self.obj, Group):
            kwargs = {"group_id": self.obj.id, "user_id": user.id}

            actions["remove"] = url_for("api.remove_group_member", **kwargs)
            actions["change"] = url_for("api.change_group_member", **kwargs)
        else:
            object_name = self.obj.__tablename__
            kwargs = {f"{object_name}_id": self.obj.id, "user_id": user.id}

            actions["remove"] = url_for(f"api.remove_{object_name}_user_role", **kwargs)
            actions["change"] = url_for(f"api.change_{object_name}_user_role", **kwargs)

        return actions

    def dump_from_iterable(self, iterable):
        """Serialize an iterable containing user roles.

        :param iterable: An iterable yielding tuples each containing a user and a
            corresponding role object.
        :return: The serialized output.
        """
        user_roles = [{"user": user, "role": role} for user, role in iterable]
        return self.dump(user_roles, many=True)


class GroupResourceRoleSchema(BaseResourceRoleSchema):
    """Schema to represent group roles.

    :param obj: (optional) An object that the current group role refers to. An instance
        of :class:`.Record`, :class:`.Collection` or :class:`.Template`. See also
        :class:`BaseResourceRoleSchema`.
    """

    group = fields.Nested("GroupSchema", required=True)

    def _generate_actions(self, obj):
        actions = {}

        try:
            group = getattr(obj, "group")
        except:
            group = obj.get("group")

        if group is None or self.obj is None:
            return actions

        object_name = self.obj.__tablename__
        kwargs = {f"{object_name}_id": self.obj.id, "group_id": group.id}

        actions["remove"] = url_for(f"api.remove_{object_name}_group_role", **kwargs)
        actions["change"] = url_for(f"api.change_{object_name}_group_role", **kwargs)

        return actions

    def dump_from_iterable(self, iterable):
        """Serialize an iterable containing group roles.

        :param iterable: An iterable yielding tuples each containing a group and a
            corresponding role object.
        :return: The serialized output.
        """
        group_roles = [{"group": group, "role": role} for group, role in iterable]
        return self.dump(group_roles, many=True)


class ResourceRoleDataSchema(BaseSchema):
    """Schema to represent the data of user or group resource roles.

    Mainly useful in combination with :func:`kadi.lib.resources.views.update_roles` and
    within templates.

    :param roles: A list of valid role values.
    :param allow_none: (optional) Whether to allow ``None`` as a valid role value.
    """

    subject_type = fields.String(required=True, validate=OneOf(["user", "group"]))

    subject_id = fields.Integer(required=True, validate=Range(min=1))

    role = fields.String(required=True, allow_none=True)

    @validates("role")
    def _validate_role(self, value):
        if value is None:
            if not self.allow_none:
                raise ValidationError("Field may not be null.")

            return

        if value not in self.roles:
            raise ValidationError(f"Must be one of: {', '.join(self.roles)}.")

    def __init__(self, roles, allow_none=False, **kwargs):
        super().__init__(**kwargs)

        self.roles = set(roles)
        self.allow_none = allow_none


def check_duplicate_identifier(model, identifier, exclude=None):
    """Check for a duplicate identifier in a schema.

    :param model: The model class to check the identifier of. One of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param identifier: The identifier to check.
    :param exclude: (optional) An instance of the model that should be excluded in the
        check.
    """
    obj_to_check = model.query.filter_by(identifier=identifier).first()

    if obj_to_check is not None and (exclude is None or exclude != obj_to_check):
        raise ValidationError("Identifier is already in use.")
