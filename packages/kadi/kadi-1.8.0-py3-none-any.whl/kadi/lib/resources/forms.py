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
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from flask_babel import ngettext
from flask_login import current_user
from marshmallow import ValidationError
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import StopValidation

import kadi.lib.constants as const
from kadi.lib.conversion import empty_str
from kadi.lib.conversion import lower
from kadi.lib.conversion import normalize
from kadi.lib.conversion import strip
from kadi.lib.forms import BaseForm
from kadi.lib.forms import DynamicMultiSelectField
from kadi.lib.forms import JSONField
from kadi.lib.forms import LFTextAreaField
from kadi.lib.forms import SelectField
from kadi.lib.forms import StringField
from kadi.lib.forms import validate_identifier
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.utils import get_group_roles
from kadi.lib.permissions.utils import get_user_roles
from kadi.modules.accounts.models import User
from kadi.modules.groups.models import Group

from .schemas import ResourceRoleDataSchema


class TagsField(DynamicMultiSelectField):
    """Custom dynamic multi select field for tagging resources.

    Tags must not be empty, are automatically converted to lowercase and whitespaces are
    stripped and normalized. Additionally, the result will be sorted and duplicate tags
    will be filtered out.

    :param max_len: (optional) The maximum length of each tag.
    """

    def __init__(self, *args, max_len=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_len = max_len

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)

        if valuelist:
            tags = []

            for tag in self.data:
                for converter in [lower, normalize]:
                    tag = converter(tag)

                if not tag:
                    self.data = self.default
                    raise ValueError(_("Tags must not be empty."))

                if self.max_len is not None and len(tag) > self.max_len:
                    self.data = self.default
                    raise ValueError(
                        ngettext(
                            "Tags cannot be longer than %(num)d character.",
                            "Tags cannot be longer than %(num)d characters.",
                            self.max_len,
                        )
                    )

                if tag not in tags:
                    tags.append(tag)

            self.data = sorted(tags)


class RolesField(JSONField):
    """Custom field to process and validate user and group roles of resources.

    Uses :class:`.ResourceRoleDataSchema` for its validation.

    :param roles: A list of roles, each item consisting of a tuple containing the actual
        role value and title to be displayed, similar to the choices in select fields.
    :param allow_none: (optional) Whether to allow ``None`` as a valid role value.
    """

    def __init__(self, *args, roles, allow_none=False, **kwargs):
        kwargs["default"] = []
        super().__init__(*args, **kwargs)

        self.roles = roles
        self.allow_none = allow_none
        self.initial = []

    def _value(self):
        return self.initial

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)

        if valuelist:
            try:
                roles = [r for r, _ in self.roles]
                schema = ResourceRoleDataSchema(
                    roles, many=True, allow_none=self.allow_none
                )
                self.data = schema.load(self.data)

            except ValidationError as e:
                self.data = self.default
                raise ValueError("Invalid data structure.") from e

    def to_dict(self):
        data = super().to_dict()

        data["roles"] = [(val, str(title)) for val, title in self.roles]
        data["allow_none"] = self.allow_none

        return data

    def set_initial_data(
        self, data=None, resource=None, user=None, keep_user_roles=False
    ):
        """Set the initial data of this field.

        :param data: (optional) The form data to use for prefilling. Defaults to the
            submitted data of the current field instance.
        :param resource: (optional) An existing resource, which can be used to set the
            initial data instead of the given form data. One of :class:`.Record`,
            :class:`.Collection` or :class:`.Template`.
        :param user: (optional) A user that will be used for checking various access
            permissions when setting the data. Defaults to the current user.
        :param keep_user_roles: (optional) Flag indicating whether to keep any roles of
            the given user.
        """
        data = data if data is not None else getattr(self, "data", [])
        user = user if user is not None else current_user

        initial_data = []

        if resource is not None:
            for _user, role in get_user_roles(
                resource.__tablename__, object_id=resource.id
            ):
                if keep_user_roles or _user != user:
                    initial_data.append(
                        {
                            "subject_type": "user",
                            "subject": [_user.id, f"@{_user.identity.username}"],
                            "role": role.name,
                        }
                    )

            for group, role in get_group_roles(
                resource.__tablename__, object_id=resource.id
            ):
                # Exclude any group that is not readable by the given user.
                if group is not None and has_permission(
                    user, "read", "group", group.id
                ):
                    initial_data.append(
                        {
                            "subject_type": "group",
                            "subject": [group.id, f"@{group.identifier}"],
                            "role": role.name,
                        }
                    )
        else:
            for role_meta in data:
                subject = None

                if role_meta["subject_type"] == "user":
                    _user = User.query.get_active(role_meta["subject_id"])

                    if _user is not None and (keep_user_roles or _user != user):
                        subject = [_user.id, f"@{_user.identity.username}"]
                else:
                    group = Group.query.get_active(role_meta["subject_id"])

                    # Exclude any group that is not readable by the given user.
                    if group is not None and has_permission(
                        user, "read", "group", group.id
                    ):
                        subject = [group.id, f"@{group.identifier}"]

                if subject is not None:
                    initial_data.append(
                        {
                            "subject_type": role_meta["subject_type"],
                            "subject": subject,
                            "role": role_meta["role"],
                        }
                    )

        self.initial = initial_data


class BaseResourceForm(BaseForm):
    """Base form class for use in creating or updating different kinds of resources.

    These resources may refer to instances of :class:`.Record`, :class:`.Collection`,
    :class:`.Template` or :class:`.Group`.
    """

    title = StringField(
        _l("Title"),
        filters=[normalize],
        validators=[
            DataRequired(),
            Length(max=const.RESOURCE_TITLE_MAX_LEN),
        ],
    )

    description = LFTextAreaField(
        _l("Description"),
        filters=[empty_str, strip],
        validators=[Length(max=const.RESOURCE_DESCRIPTION_MAX_LEN)],
    )

    @staticmethod
    def identifier_field(**kwargs):
        """Factory method to create a basic resource identifier field."""
        return StringField(
            _l("Identifier"),
            filters=[lower, strip],
            validators=[
                DataRequired(),
                Length(max=const.RESOURCE_IDENTIFIER_MAX_LEN),
                validate_identifier,
            ],
            **kwargs,
        )

    @staticmethod
    def visibility_field(**kwargs):
        """Factory method to create a basic resource visibility field."""
        return SelectField(
            _l("Visibility"),
            choices=[
                (const.RESOURCE_VISIBILITY_PRIVATE, _l("Private")),
                (const.RESOURCE_VISIBILITY_PUBLIC, _l("Public")),
            ],
            **kwargs,
        )


def check_duplicate_identifier(model, identifier, exclude=None):
    """Check for a duplicate identifier in a form.

    :param model: The model class to check the identifier of. One of :class:`.Record`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    :param identifier: The identifier to check.
    :param exclude: (optional) An instance of the model that should be excluded in the
        check.
    """
    obj_to_check = model.query.filter_by(identifier=identifier).first()

    if obj_to_check is not None and (exclude is None or exclude != obj_to_check):
        raise StopValidation(_("Identifier is already in use."))
