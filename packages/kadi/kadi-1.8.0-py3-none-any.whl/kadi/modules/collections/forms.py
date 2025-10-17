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

from flask_babel import lazy_gettext as _l
from flask_login import current_user
from wtforms.validators import DataRequired

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.forms import BaseForm
from kadi.lib.forms import DynamicMultiSelectField
from kadi.lib.forms import DynamicSelectField
from kadi.lib.forms import SubmitField
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.permissions.core import has_permission
from kadi.lib.resources.forms import BaseResourceForm
from kadi.lib.resources.forms import RolesField
from kadi.lib.resources.forms import TagsField
from kadi.lib.resources.forms import check_duplicate_identifier
from kadi.lib.tags.models import Tag
from kadi.modules.records.models import Record
from kadi.modules.records.models import RecordState
from kadi.modules.templates.models import Template
from kadi.modules.templates.models import TemplateType

from .models import Collection


class BaseCollectionForm(BaseResourceForm):
    """Base form class for use in creating or updating collections.

    :param import_data: (optional) A dictionary containing data imported from a file
        used for prefilling the form.
    :param collection: (optional) A collection used for prefilling the form.
    :param user: (optional) A user that will be used for checking various access
        permissions when prefilling the form. Defaults to the current user.
    """

    identifier = BaseResourceForm.identifier_field(
        description=_l("Unique identifier of this collection.")
    )

    visibility = BaseResourceForm.visibility_field(
        description=_l(
            "Public visibility automatically grants EVERY logged-in user read"
            " permissions for this collection."
        )
    )

    tags = TagsField(
        _l("Tags"),
        max_len=Tag.Meta.check_constraints["name"]["length"]["max"],
        description=_l(
            "An optional list of keywords further describing the collection."
        ),
    )

    record_template = DynamicSelectField(
        _l("Default record template"),
        coerce=int,
        description=_l(
            "A record template that will be used as a default when adding new records"
            " to this collection."
        ),
    )

    def _check_template_permission(self, template):
        return has_permission(self.user, "read", "template", template.id)

    def _prefill_tags(self, tags):
        if tags is not None:
            self.tags.initial = [(tag, tag) for tag in sorted(tags)]

    def _prefill_record_template(self, template):
        if template is None:
            return

        if not isinstance(template, Template):
            template = Template.query.get_active(template)

        if (
            template is not None
            and template.type == TemplateType.RECORD
            and self._check_template_permission(template)
        ):
            self.record_template.initial = (template.id, f"@{template.identifier}")

    def __init__(self, *args, import_data=None, collection=None, user=None, **kwargs):
        self.user = user if user is not None else current_user

        # Prefill all simple fields directly.
        accessor = None

        if import_data is not None:
            accessor = import_data.get
        elif collection is not None:
            accessor = partial(getattr, collection)

        if accessor is not None:
            kwargs["data"] = {
                "title": accessor("title", ""),
                "identifier": accessor("identifier", ""),
                "description": accessor("description", ""),
                "visibility": accessor("visibility", const.RESOURCE_VISIBILITY_PRIVATE),
            }

        super().__init__(*args, **kwargs)

        # Prefill all other fields separately, also taking into account whether the form
        # was submitted. However, check for import data first, as the default form
        # submission check only considers the current HTTP request method.
        if import_data is not None:
            self._prefill_tags(import_data.get("tags"))

        elif self.is_submitted():
            self._prefill_tags(self.tags.data)
            self._prefill_record_template(self.record_template.data)

        elif collection is not None:
            self._prefill_tags([tag.name for tag in collection.tags])
            self._prefill_record_template(collection.record_template)


class NewCollectionForm(BaseCollectionForm):
    """A form for use in creating new collections.

    :param collection: (optional) See :class:`BaseCollectionForm`.
    :param user: (optional) See :class:`BaseCollectionForm`.
    """

    records = DynamicMultiSelectField(
        _l("Linked records"),
        coerce=int,
        description=_l("Directly link this collection with one or more records."),
    )

    parent_collection = DynamicSelectField(
        _l("Parent collection"),
        coerce=int,
        description=_l("Directly link this collection with a parent collection."),
    )

    roles = RolesField(
        _l("Permissions"),
        roles=[(r, r.capitalize()) for r in Collection.Meta.permissions["roles"]],
        description=_l("Directly add user or group roles to this collection."),
    )

    submit = SubmitField(_l("Create collection"))

    def _prefill_records(self, records):
        self.records.initial = [(r.id, f"@{r.identifier}") for r in records]

    def _prefill_parent_collection(self, collection, user):
        if collection is None:
            return

        if not isinstance(collection, Collection):
            collection = Collection.query.get_active(collection)

        if collection is not None and has_permission(
            user, "link", "collection", collection.id
        ):
            self.parent_collection.initial = (
                collection.id,
                f"@{collection.identifier}",
            )

    def __init__(self, *args, collection=None, user=None, **kwargs):
        user = user if user is not None else current_user

        super().__init__(*args, collection=collection, user=user, **kwargs)

        linkable_record_ids = (
            get_permitted_objects(user, "link", "record")
            .filter(Record.state == RecordState.ACTIVE)
            .with_entities(Record.id)
        )

        if self.is_submitted():
            if self.records.data:
                records = Record.query.filter(
                    db.and_(
                        Record.id.in_(linkable_record_ids),
                        Record.id.in_(self.records.data),
                    )
                )
                self._prefill_records(records)

            self._prefill_parent_collection(self.parent_collection.data, user=user)
            self.roles.set_initial_data(user=user)

        elif collection is not None:
            records = collection.records.filter(Record.id.in_(linkable_record_ids))
            self._prefill_records(records)

            self._prefill_parent_collection(collection.parent, user=user)
            self.roles.set_initial_data(resource=collection, user=user)

    def validate_identifier(self, field):
        # pylint: disable=missing-function-docstring
        check_duplicate_identifier(Collection, field.data)


class EditCollectionForm(BaseCollectionForm):
    """A form for use in editing existing collections.

    :param collection: The collection to edit, used for prefilling the form.
    """

    submit = SubmitField(_l("Save changes"))

    submit_quit = SubmitField(_l("Save changes and quit"))

    def _check_template_permission(self, template):
        # See "modules.collections.core.update_collection" on why this special check is
        # done here.
        return (
            has_permission(self.user, "read", "template", template.id)
            or self.collection.record_template == template
        )

    def __init__(self, collection, *args, **kwargs):
        self.collection = collection
        super().__init__(*args, collection=collection, **kwargs)

    def validate_identifier(self, field):
        # pylint: disable=missing-function-docstring
        check_duplicate_identifier(Collection, field.data, exclude=self.collection)


class LinkRecordsForm(BaseForm):
    """A form for use in linking collections with records."""

    records = DynamicMultiSelectField(
        _l("Records"), validators=[DataRequired()], coerce=int
    )

    submit = SubmitField(_l("Link records"))


class LinkCollectionsForm(BaseForm):
    """A form for use in linking collections with other collections."""

    collections = DynamicMultiSelectField(
        _l("Collections"), validators=[DataRequired()], coerce=int
    )

    submit = SubmitField(_l("Link collections"))


class AddCollectionRolesForm(BaseForm):
    """A form for use in adding user or group roles to a collection."""

    roles = RolesField(
        _l("New permissions"),
        roles=[(r, r.capitalize()) for r in Collection.Meta.permissions["roles"]],
    )

    submit = SubmitField(_l("Add permissions"))


class UpdateRecordsRolesForm(BaseForm):
    """A form for use in updating user or group roles of linked records."""

    roles = RolesField(
        _l("New permissions"),
        roles=[(r, r.capitalize()) for r in Record.Meta.permissions["roles"]],
        allow_none=True,
    )

    submit = SubmitField(_l("Apply permissions"))
