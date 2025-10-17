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
from flask import current_app
from flask_babel import lazy_gettext as _l
from wtforms.validators import DataRequired

from kadi.lib.forms import BaseForm
from kadi.lib.forms import BooleanField
from kadi.lib.forms import FileField
from kadi.lib.forms import SelectField
from kadi.lib.forms import StringField
from kadi.lib.forms import SubmitField
from kadi.lib.resources.forms import BaseResourceForm
from kadi.lib.resources.forms import RolesField
from kadi.lib.resources.forms import check_duplicate_identifier

from .models import Group


class BaseGroupForm(BaseResourceForm):
    """Base form class for use in creating or updating groups."""

    identifier = BaseResourceForm.identifier_field(
        description=_l("Unique identifier of this group.")
    )

    visibility = BaseResourceForm.visibility_field(
        description=_l(
            "Public visibility automatically grants EVERY logged-in user read"
            " permissions for this group."
        )
    )

    image = FileField(_l("Image"))


class NewGroupForm(BaseGroupForm):
    """A form for use in creating new groups."""

    submit = SubmitField(_l("Create group"))

    def validate_identifier(self, field):
        # pylint: disable=missing-function-docstring
        check_duplicate_identifier(Group, field.data)


class EditGroupForm(BaseGroupForm):
    """A form for use in editing existing groups.

    :param group: The group to edit, used for prefilling the form.
    """

    remove_image = BooleanField(_l("Remove current image"))

    submit = SubmitField(_l("Save changes"))

    submit_quit = SubmitField(_l("Save changes and quit"))

    def __init__(self, group, *args, **kwargs):
        self.group = group
        super().__init__(*args, obj=group, **kwargs)

    def validate_identifier(self, field):
        # pylint: disable=missing-function-docstring
        check_duplicate_identifier(Group, field.data, exclude=self.group)


class AddMembersForm(BaseForm):
    """A form for use in adding members (i.e. user roles) to a group."""

    roles = RolesField(
        _l("New members"),
        roles=[(r, r.capitalize()) for r in Group.Meta.permissions["roles"]],
    )

    submit = SubmitField(_l("Add members"))


class AddRulesForm(BaseForm):
    """A form for use in adding new username role rules for groups."""

    role = SelectField(
        _l("Role"),
        choices=[(r, r.capitalize()) for r in Group.Meta.permissions["roles"]],
    )

    identity_type = SelectField(_l("Account type"), choices=[])

    username = StringField(
        _l("Username"),
        validators=[DataRequired()],
        description=_l("Supports wildcards (e.g. *@*.example.edu)."),
    )

    retroactive = BooleanField(_l("Apply retroactively"))

    submit = SubmitField(_l("Add rule"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = []

        for provider_type, provider_config in current_app.config[
            "AUTH_PROVIDERS"
        ].items():
            identity_name = str(
                provider_config["identity_class"].Meta.identity_type["name"]
            )
            choices.append((provider_type, identity_name))

        self.identity_type.choices = choices
