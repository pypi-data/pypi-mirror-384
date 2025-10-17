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
from functools import partial

from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from flask_login import current_user
from marshmallow import ValidationError
from wtforms.validators import Length
from wtforms.validators import StopValidation

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.conversion import empty_str
from kadi.lib.conversion import lower
from kadi.lib.conversion import normalize
from kadi.lib.conversion import strip
from kadi.lib.forms import BaseForm
from kadi.lib.forms import DynamicMultiSelectField
from kadi.lib.forms import DynamicSelectField
from kadi.lib.forms import LFTextAreaField
from kadi.lib.forms import StringField
from kadi.lib.forms import SubmitField
from kadi.lib.forms import validate_identifier
from kadi.lib.licenses.models import License
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.resources.forms import BaseResourceForm
from kadi.lib.resources.forms import RolesField
from kadi.lib.resources.forms import TagsField
from kadi.lib.resources.forms import check_duplicate_identifier
from kadi.lib.tags.models import Tag
from kadi.modules.collections.models import Collection
from kadi.modules.collections.models import CollectionState
from kadi.modules.records.extras import ExtrasField
from kadi.modules.records.extras import remove_extra_values
from kadi.modules.records.forms import RecordLinksField
from kadi.modules.records.models import Record

from .models import Template
from .schemas import RecordTemplateDataSchema


class BaseTemplateForm(BaseResourceForm):
    """Base form class for use in creating or updating templates.

    :param import_data: (optional) A dictionary containing data imported from a file
        used for prefilling the form.
    :param template: (optional) A template used for prefilling the form, which must be
        of the correct type corresponding to each form class.
    """

    identifier = BaseResourceForm.identifier_field(
        description=_l("Unique identifier of this template.")
    )

    visibility = BaseResourceForm.visibility_field(
        description=_l(
            "Public visibility automatically grants EVERY logged-in user read"
            " permissions for this template."
        )
    )

    def __init__(self, *args, import_data=None, template=None, **kwargs):
        data = None
        accessor = None

        if import_data is not None:
            accessor = import_data.get
        elif template is not None:
            accessor = partial(getattr, template)

        if accessor is not None:
            data = {
                "title": accessor("title", ""),
                "identifier": accessor("identifier", ""),
                "description": accessor("description", ""),
                "visibility": accessor("visibility", const.RESOURCE_VISIBILITY_PRIVATE),
            }

        if not kwargs.get("data"):
            kwargs["data"] = data
        elif data is not None:
            kwargs["data"].update(data)

        super().__init__(*args, **kwargs)

    @property
    def template_data(self):
        """Get the collected template data.

        The data may optionally be validated again. If it is invalid, ``None`` should be
        returned instead.
        """
        return None


class BaseRecordTemplateForm(BaseTemplateForm):
    """Base form class for use in creating or updating record templates.

    :param import_data: (optional) See :class:`BaseTemplateForm`.
    :param template: (optional) See :class:`BaseTemplateForm`.
    :param record: (optional) A record used for prefilling the template data.
    :param user: (optional) A user that will be used for checking various access
        permissions when prefilling the form. Defaults to the current user.
    """

    record_title = StringField(
        _l("Title"),
        filters=[normalize, empty_str],
        validators=[Length(max=const.RESOURCE_TITLE_MAX_LEN)],
    )

    record_identifier = StringField(
        _l("Identifier"),
        filters=[lower, strip, empty_str],
        validators=[Length(max=const.RESOURCE_IDENTIFIER_MAX_LEN)],
        description=_l("Unique identifier of a record."),
    )

    record_type = DynamicSelectField(
        _l("Type"),
        filters=[lower, normalize],
        validators=[Length(max=Record.Meta.check_constraints["type"]["length"]["max"])],
        description=_l(
            "Optional type of a record, e.g. dataset, experimental device, etc."
        ),
    )

    record_description = LFTextAreaField(
        _l("Description"),
        filters=[empty_str, strip],
        validators=[Length(max=const.RESOURCE_DESCRIPTION_MAX_LEN)],
    )

    record_license = DynamicSelectField(
        _l("License"), description=_l("Optional license of a record.")
    )

    record_tags = TagsField(
        _l("Tags"),
        max_len=Tag.Meta.check_constraints["name"]["length"]["max"],
        description=_l("An optional list of keywords further describing a record."),
    )

    record_extras = ExtrasField(_l("Extra metadata"), is_template=True)

    record_collections = DynamicMultiSelectField(
        _l("Collections"),
        coerce=int,
        description=_l("Directly link a record with one or more collections."),
    )

    record_links = RecordLinksField(
        _l("Record links"),
        description=_l("Directly link a record with one or more other records."),
    )

    record_roles = RolesField(
        _l("Permissions"),
        roles=[(r, r.capitalize()) for r in Record.Meta.permissions["roles"]],
        description=_l("Directly add user or group roles to a record."),
    )

    def _prefill_record_type(self, type_data):
        if type_data is not None:
            self.record_type.initial = (type_data, type_data)

    def _prefill_record_license(self, license):
        if license is None:
            return

        if not isinstance(license, License):
            license = License.query.filter_by(name=license).first()

        if license is not None:
            self.record_license.initial = (license.name, license.title)

    def _prefill_record_tags(self, tags):
        if tags is not None:
            self.record_tags.initial = [(tag, tag) for tag in sorted(tags)]

    def _prefill_record_collections(self, collections):
        self.record_collections.initial = [
            (c.id, f"@{c.identifier}") for c in collections
        ]

    def __init__(
        self, *args, import_data=None, template=None, record=None, user=None, **kwargs
    ):
        user = user if user is not None else current_user

        # Prefill all simple fields directly.
        accessor = None

        if import_data is not None:
            accessor = import_data.get("data", {}).get
        elif template is not None:
            accessor = template.data.get
        elif record is not None:
            accessor = partial(getattr, record)

        if accessor is not None:
            kwargs["data"] = {
                "record_title": accessor("title", ""),
                "record_identifier": accessor("identifier", ""),
                "record_description": accessor("description", ""),
                "record_extras": accessor("extras", []),
            }

            # Remove the values of extras when copying record metadata.
            if record is not None:
                kwargs["data"]["record_extras"] = remove_extra_values(
                    kwargs["data"]["record_extras"]
                )

        super().__init__(*args, import_data=import_data, template=template, **kwargs)

        # Prefill all other fields separately, also taking into account whether the form
        # was submitted.
        linkable_collection_ids = (
            get_permitted_objects(user, "link", "collection")
            .filter(Collection.state == CollectionState.ACTIVE)
            .with_entities(Collection.id)
        )

        # Check for import data first, as the default form submission check only
        # considers the current HTTP request method.
        if import_data is not None:
            template_data = import_data.get("data", {})

            self._prefill_record_type(template_data.get("type"))
            self._prefill_record_license(template_data.get("license"))
            self._prefill_record_tags(template_data.get("tags"))

        elif self.is_submitted():
            self._prefill_record_type(self.record_type.data)
            self._prefill_record_license(self.record_license.data)
            self._prefill_record_tags(self.record_tags.data)

            if self.record_collections.data:
                collections = Collection.query.filter(
                    db.and_(
                        Collection.id.in_(linkable_collection_ids),
                        Collection.id.in_(self.record_collections.data),
                    )
                )
                self._prefill_record_collections(collections)

            self.record_links.set_initial_data(user=user)
            self.record_roles.set_initial_data(user=user, keep_user_roles=True)

        elif template is not None:
            self._prefill_record_type(template.data.get("type"))
            self._prefill_record_license(template.data.get("license"))
            self._prefill_record_tags(template.data.get("tags"))

            if template.data.get("collections"):
                collections = Collection.query.filter(
                    db.and_(
                        Collection.id.in_(linkable_collection_ids),
                        Collection.id.in_(template.data["collections"]),
                    )
                )
                self._prefill_record_collections(collections)

            self.record_links.set_initial_data(
                data=template.data.get("record_links", []), user=user
            )
            self.record_roles.set_initial_data(
                data=template.data.get("roles", []), user=user, keep_user_roles=True
            )

        elif record is not None:
            self._prefill_record_type(record.type)
            self._prefill_record_license(record.license)
            self._prefill_record_tags([tag.name for tag in record.tags])

            collections = record.collections.filter(
                Collection.id.in_(linkable_collection_ids)
            )
            self._prefill_record_collections(collections)

            self.record_links.set_initial_data(record=record, user=user)
            self.record_roles.set_initial_data(resource=record, user=user)

    def validate_record_identifier(self, field):
        # pylint: disable=missing-function-docstring
        if field.data:
            validate_identifier(self, field)

    def validate_record_license(self, field):
        # pylint: disable=missing-function-docstring
        if (
            field.data is not None
            and License.query.filter_by(name=field.data).first() is None
        ):
            raise StopValidation(_("Not a valid license."))

    @property
    def template_data(self):
        data = {
            "title": self.record_title.data,
            "identifier": self.record_identifier.data,
            "type": self.record_type.data,
            "description": self.record_description.data,
            "license": self.record_license.data,
            "tags": self.record_tags.data,
            "extras": self.record_extras.data,
            "collections": self.record_collections.data,
            "record_links": self.record_links.data,
            "roles": self.record_roles.data,
        }

        try:
            # Validate the collected data with the corresponding schema again to ensure
            # it is consistent.
            data = RecordTemplateDataSchema().load(data)
        except ValidationError:
            return None

        return data


class BaseExtrasTemplateForm(BaseTemplateForm):
    """Base form class for use in creating or updating extras templates.

    :param import_data: (optional) See :class:`BaseTemplateForm`.
    :param template: (optional) See :class:`BaseTemplateForm`.
    :param record: (optional) A record used for prefilling the template data.
    """

    extras = ExtrasField(_l("Extra metadata"), is_template=True)

    def __init__(self, *args, import_data=None, template=None, record=None, **kwargs):
        if import_data is not None:
            kwargs["data"] = {"extras": import_data.get("data", [])}
        elif template is not None:
            kwargs["data"] = {"extras": template.data}
        elif record is not None:
            kwargs["data"] = {"extras": remove_extra_values(record.extras)}

        super().__init__(*args, import_data=import_data, template=template, **kwargs)

    @property
    def template_data(self):
        return self.extras.data


class NewTemplateFormMixin:
    """Mixin class for forms used in creating new templates.

    :param template: (optional) See :class:`BaseTemplateForm`.
    :param user: (optional) A user that will be used for checking various access
        permissions when prefilling the form. Defaults to the current user.
    """

    roles = RolesField(
        _l("Permissions"),
        roles=[(r, r.capitalize()) for r in Template.Meta.permissions["roles"]],
        description=_l("Directly add user or group roles to this template."),
    )

    submit = SubmitField(_l("Create template"))

    def __init__(self, *args, template=None, user=None, **kwargs):
        user = user if user is not None else current_user

        super().__init__(*args, template=template, user=user, **kwargs)

        if self.is_submitted():
            self.roles.set_initial_data(user=user)
        elif template is not None:
            self.roles.set_initial_data(resource=template, user=user)

    def validate_identifier(self, field):
        # pylint: disable=missing-function-docstring
        check_duplicate_identifier(Template, field.data)


class NewRecordTemplateForm(NewTemplateFormMixin, BaseRecordTemplateForm):
    """A form for use in creating new record templates."""


class NewExtrasTemplateForm(NewTemplateFormMixin, BaseExtrasTemplateForm):
    """A form for use in creating new extras templates."""


class EditTemplateFormMixin:
    """Mixin class for forms used in editing existing templates.

    :param template: The template to edit, used for prefilling the form.
    """

    submit = SubmitField(_l("Save changes"))

    submit_quit = SubmitField(_l("Save changes and quit"))

    def __init__(self, template, *args, **kwargs):
        self.template = template
        super().__init__(*args, template=template, **kwargs)

    def validate_identifier(self, field):
        # pylint: disable=missing-function-docstring
        check_duplicate_identifier(Template, field.data, exclude=self.template)


class EditRecordTemplateForm(EditTemplateFormMixin, BaseRecordTemplateForm):
    """A form for use in updating record templates."""


class EditExtrasTemplateForm(EditTemplateFormMixin, BaseExtrasTemplateForm):
    """A form for use in updating extras templates."""


class AddRolesForm(BaseForm):
    """A form for use in adding user or group roles to a template."""

    roles = RolesField(
        _l("New permissions"),
        roles=[(r, r.capitalize()) for r in Template.Meta.permissions["roles"]],
    )

    submit = SubmitField(_l("Add permissions"))
