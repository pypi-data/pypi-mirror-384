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
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import StopValidation

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.conversion import empty_str
from kadi.lib.conversion import lower
from kadi.lib.conversion import none
from kadi.lib.conversion import normalize
from kadi.lib.conversion import strip
from kadi.lib.forms import BaseForm
from kadi.lib.forms import DynamicMultiSelectField
from kadi.lib.forms import DynamicSelectField
from kadi.lib.forms import JSONField
from kadi.lib.forms import LFTextAreaField
from kadi.lib.forms import StringField
from kadi.lib.forms import SubmitField
from kadi.lib.forms import convert_schema_validation_msg
from kadi.lib.forms import validate_iri
from kadi.lib.forms import validate_mimetype
from kadi.lib.licenses.models import License
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.permissions.core import has_permission
from kadi.lib.resources.forms import BaseResourceForm
from kadi.lib.resources.forms import RolesField
from kadi.lib.resources.forms import TagsField
from kadi.lib.resources.forms import check_duplicate_identifier
from kadi.lib.tags.models import Tag
from kadi.modules.collections.models import Collection
from kadi.modules.collections.models import CollectionState
from kadi.modules.records.links import get_permitted_record_links
from kadi.modules.templates.models import TemplateType

from .extras import ExtrasField
from .links import get_linked_record
from .models import File
from .models import FileState
from .models import Record
from .models import RecordLink
from .schemas import RecordLinkDataSchema


class RecordLinksField(JSONField):
    """Custom field to process and validate record links.

    Uses :class:`.RecordLinkDataSchema` for its validation.
    """

    def __init__(self, *args, **kwargs):
        kwargs["default"] = []
        super().__init__(*args, **kwargs)

        self.initial = []
        self._validation_errors = {}

    def _value(self):
        return self.initial

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)

        if valuelist:
            try:
                schema = RecordLinkDataSchema(many=True)
                self.data = schema.load(self.data)

            except ValidationError as e:
                self._validation_errors = e.messages

                # Check if at least the basic structure of the data is valid and discard
                # it otherwise.
                if not isinstance(self.data, list):
                    self.data = self.default
                    self._validation_errors = {}
                else:
                    for item in self.data:
                        if not isinstance(item, dict):
                            self.data = self.default
                            self._validation_errors = {}
                            break

                raise ValueError("Invalid data structure.") from e

    def to_dict(self):
        data = super().to_dict()

        constraints = RecordLink.Meta.check_constraints
        max_term_len = constraints["term"]["length"]["max"]

        data["validation"]["max"] = {
            "name": constraints["name"]["length"]["max"],
            "term": max_term_len,
        }
        data["errors"] = self._validation_errors

        for error_data in data["errors"].values():
            for field_name, error_msgs in error_data.items():
                for index, error_msg in enumerate(error_msgs):
                    interpolations = {}

                    if field_name == "term":
                        interpolations["max"] = max_term_len

                    error_msgs[index] = convert_schema_validation_msg(
                        error_msg, **interpolations
                    )

        return data

    def set_initial_data(self, data=None, record=None, user=None):
        """Set the initial data of this field.

        :param data: (optional) The form data to use for prefilling. Defaults to the
            submitted data of the current field instance.
        :param record: (optional) An existing record, which can be used to set the
            initial data instead of the given form data.
        :param user: (optional) A user that will be used for checking various access
            permissions when setting the data. Defaults to the current user.
        """
        data = data if data is not None else getattr(self, "data", [])
        user = user if user is not None else current_user

        initial_data = []

        if record is not None:
            record_links_query = get_permitted_record_links(
                record, actions=["link"], user=user
            ).order_by(RecordLink.created_at)

            for record_link in record_links_query:
                if record_link.record_from_id == record.id:
                    direction = "out"
                    linked_record = record_link.record_to
                else:
                    direction = "in"
                    linked_record = record_link.record_from

                initial_data.append(
                    {
                        "direction": direction,
                        "record": [linked_record.id, f"@{linked_record.identifier}"],
                        "name": record_link.name,
                        "term": record_link.term,
                    }
                )
        else:
            # Make sure to not rely on the data contents, as invalid (submitted) form
            # data is only discarded if the overall structure is invalid.
            for link_meta in data:
                linked_record_data = None
                record_id = link_meta.get("record")

                # pylint: disable=unidiomatic-typecheck
                if type(record_id) is int:
                    linked_record = Record.query.get_active(record_id)

                    if linked_record is not None and has_permission(
                        user, "link", "record", linked_record.id
                    ):
                        linked_record_data = [
                            linked_record.id,
                            f"@{linked_record.identifier}",
                        ]

                initial_data.append(
                    {
                        "direction": link_meta.get("direction", "out"),
                        "record": linked_record_data,
                        "name": link_meta.get("name"),
                        "term": link_meta.get("term"),
                    }
                )

        self.initial = initial_data


class BaseRecordForm(BaseResourceForm):
    """Base form class for use in creating or updating records.

    :param import_data: (optional) A dictionary containing data imported from a file
        used for prefilling the form.
    :param record: (optional) A record used for prefilling the form.
    :param template: (optional) A record or extras template used for prefilling the
        form.
    """

    identifier = BaseResourceForm.identifier_field(
        description=_l("Unique identifier of this record.")
    )

    type = DynamicSelectField(
        _l("Type"),
        filters=[lower, normalize],
        validators=[Length(max=Record.Meta.check_constraints["type"]["length"]["max"])],
        description=_l(
            "Optional type of this record, e.g. dataset, experimental device, etc."
        ),
    )

    license = DynamicSelectField(
        _l("License"),
        description=_l(
            "Specifying an optional license can determine the conditions for the"
            " correct reuse of data and metadata when the record is published or simply"
            " shared with other users. A license can also be uploaded as a file, in"
            ' which case one of the "Other" licenses can be chosen.'
        ),
    )

    visibility = BaseResourceForm.visibility_field(
        description=_l(
            "Public visibility automatically grants EVERY logged-in user read"
            " permissions for this record."
        )
    )

    tags = TagsField(
        _l("Tags"),
        max_len=Tag.Meta.check_constraints["name"]["length"]["max"],
        description=_l("An optional list of keywords further describing the record."),
    )

    extras = ExtrasField(_l("Extra metadata"))

    def _prefill_type(self, type_data):
        if type_data is not None:
            self.type.initial = (type_data, type_data)

    def _prefill_license(self, license):
        if license is None:
            return

        if not isinstance(license, License):
            license = License.query.filter_by(name=license).first()

        if license is not None:
            self.license.initial = (license.name, license.title)

    def _prefill_tags(self, tags):
        if tags is not None:
            self.tags.initial = [(tag, tag) for tag in sorted(tags)]

    def __init__(self, *args, import_data=None, record=None, template=None, **kwargs):
        # Prefill all simple fields directly.
        accessor = None

        if import_data is not None:
            accessor = import_data.get
        elif record is not None:
            accessor = partial(getattr, record)
        elif template is not None:
            if template.type == TemplateType.RECORD:
                accessor = template.data.get
            elif template.type == TemplateType.EXTRAS:
                accessor = {"extras": template.data}.get

        if accessor is not None:
            kwargs["data"] = {
                "title": accessor("title", ""),
                "identifier": accessor("identifier", ""),
                "description": accessor("description", ""),
                "visibility": accessor("visibility", const.RESOURCE_VISIBILITY_PRIVATE),
                "extras": accessor("extras", []),
            }

        super().__init__(*args, **kwargs)

        # Prefill all other fields separately, also taking into account whether the form
        # was submitted. However, check for import data first, as the default form
        # submission check only considers the current HTTP request method.
        if import_data is not None:
            self._prefill_type(import_data.get("type"))
            self._prefill_license(import_data.get("license"))
            self._prefill_tags(import_data.get("tags"))

        elif self.is_submitted():
            self._prefill_type(self.type.data)
            self._prefill_license(self.license.data)
            self._prefill_tags(self.tags.data)

        elif record is not None:
            self._prefill_type(record.type)
            self._prefill_license(record.license)
            self._prefill_tags([tag.name for tag in record.tags])

        elif template is not None and template.type == TemplateType.RECORD:
            self._prefill_type(template.data.get("type"))
            self._prefill_license(template.data.get("license"))
            self._prefill_tags(template.data.get("tags"))

    def validate_license(self, field):
        # pylint: disable=missing-function-docstring
        if (
            field.data is not None
            and License.query.filter_by(name=field.data).first() is None
        ):
            raise StopValidation(_("Not a valid license."))


class NewRecordForm(BaseRecordForm):
    """A form for use in creating new records.

    :param record: (optional) See :class:`BaseRecordForm`.
    :param template: (optional) See :class:`BaseRecordForm`.
    :param collection: (optional) A collection used for prefilling the linked
        collections.
    :param user: (optional) A user that will be used for checking various access
        permissions when prefilling the form. Defaults to the current user.
    """

    collections = DynamicMultiSelectField(
        _l("Collections"),
        coerce=int,
        description=_l("Directly link this record with one or more collections."),
    )

    record_links = RecordLinksField(
        _l("Record links"),
        description=_l("Directly link this record with one or more other records."),
    )

    roles = RolesField(
        _l("Permissions"),
        roles=[(r, r.capitalize()) for r in Record.Meta.permissions["roles"]],
        description=_l("Directly add user or group roles to this record."),
    )

    submit = SubmitField(_l("Create record"))

    submit_files = SubmitField(_l("Create record and add files"))

    def _prefill_collections(self, collections):
        self.collections.initial = [(c.id, f"@{c.identifier}") for c in collections]

    def __init__(
        self, *args, record=None, template=None, collection=None, user=None, **kwargs
    ):
        user = user if user is not None else current_user

        super().__init__(*args, record=record, template=template, **kwargs)

        linkable_collections_ids = (
            get_permitted_objects(user, "link", "collection")
            .filter(Collection.state == CollectionState.ACTIVE)
            .with_entities(Collection.id)
        )

        if self.is_submitted():
            if self.collections.data:
                collections = Collection.query.filter(
                    db.and_(
                        Collection.id.in_(linkable_collections_ids),
                        Collection.id.in_(self.collections.data),
                    )
                )
                self._prefill_collections(collections)
            # To allow combining a predefined linked collection with (submitted) import
            # data.
            elif collection is not None:
                self._prefill_collections([collection])

            self.record_links.set_initial_data(user=user)
            self.roles.set_initial_data(user=user)
        else:
            if record is not None:
                collections = record.collections.filter(
                    Collection.id.in_(linkable_collections_ids)
                )
                self._prefill_collections(collections)

                self.record_links.set_initial_data(record=record, user=user)
                self.roles.set_initial_data(resource=record, user=user)

            elif template is not None and template.type == TemplateType.RECORD:
                if template.data.get("collections"):
                    collections = Collection.query.filter(
                        db.and_(
                            Collection.id.in_(linkable_collections_ids),
                            Collection.id.in_(template.data["collections"]),
                        )
                    )
                    self._prefill_collections(collections)

                self.record_links.set_initial_data(
                    data=template.data.get("record_links", []), user=user
                )
                self.roles.set_initial_data(
                    data=template.data.get("roles", []), user=user
                )

            # If a collection is given, overwrite all values set previously for the
            # linked collections.
            if collection is not None:
                self._prefill_collections([collection])

    def validate_identifier(self, field):
        # pylint: disable=missing-function-docstring
        check_duplicate_identifier(Record, field.data)


class EditRecordForm(BaseRecordForm):
    """A form for use in editing existing records.

    :param record: The record to edit, used for prefilling the form.
    """

    submit = SubmitField(_l("Save changes"))

    submit_quit = SubmitField(_l("Save changes and quit"))

    def __init__(self, record, *args, **kwargs):
        self.record = record
        super().__init__(*args, record=record, **kwargs)

    def validate_identifier(self, field):
        # pylint: disable=missing-function-docstring
        check_duplicate_identifier(Record, field.data, exclude=self.record)


class AddRecordLinksForm(BaseForm):
    """A form for use in creating new record links.

    :param user: (optional) A user that will be used for checking various access
        permissions when prefilling the form. Defaults to the current user.
    """

    record_links = RecordLinksField(_l("New record links"))

    submit = SubmitField(_l("Link records"))

    def __init__(self, *args, user=None, **kwargs):
        user = user if user is not None else current_user

        super().__init__(*args, **kwargs)

        if self.is_submitted():
            self.record_links.set_initial_data(user=user)


class EditRecordLinkForm(BaseForm):
    """A form for use in editing existing record links.

    :param record_link: The record link to edit, used for prefilling the form.
    :param record: The record in whose context the given record link is edited.
    :param user: (optional) A user that will be used for checking various access
        permissions when prefilling the form. Defaults to the current user.
    """

    record = DynamicSelectField(_l("Record"), validators=[DataRequired()], coerce=int)

    name = DynamicSelectField(
        _l("Name"),
        filters=[normalize],
        validators=[
            DataRequired(),
            Length(max=RecordLink.Meta.check_constraints["name"]["length"]["max"]),
        ],
        description=_l("The name of the link."),
    )

    term = StringField(
        _l("Term IRI"),
        filters=[strip, none],
        validators=[
            Length(max=RecordLink.Meta.check_constraints["term"]["length"]["max"]),
            validate_iri,
        ],
        description=_l(
            "An IRI specifying an existing term that the link should represent."
        ),
    )

    submit = SubmitField(_l("Save changes"))

    def _prefill_record(self, record, user):
        if record is None:
            return

        if not isinstance(record, Record):
            record = Record.query.get_active(record)

        if record is not None and has_permission(user, "read", "record", record.id):
            self.record.initial = (record.id, f"@{record.identifier}")

    def _prefill_name(self, name):
        if name is not None:
            self.name.initial = (name, name)

    def __init__(self, record_link, record, *args, user=None, **kwargs):
        user = user if user is not None else current_user

        # Prefill all simple fields directly.
        if record_link is not None:
            kwargs["data"] = {"term": record_link.term}

        super().__init__(*args, **kwargs)

        # Prefill all other fields separately, also taking into account whether the form
        # was submitted.
        if self.is_submitted():
            self._prefill_record(self.record.data, user)
            self._prefill_name(self.name.data)

        elif record_link is not None:
            linked_record = get_linked_record(record_link, record)

            self._prefill_record(linked_record, user)
            self._prefill_name(record_link.name)


class LinkCollectionsForm(BaseForm):
    """A form for use in linking records with collections."""

    collections = DynamicMultiSelectField(
        _l("Collections"), validators=[DataRequired()], coerce=int
    )

    submit = SubmitField(_l("Link collections"))


class AddRolesForm(BaseForm):
    """A form for use in adding user or group roles to a record."""

    roles = RolesField(
        _l("New permissions"),
        roles=[(r, r.capitalize()) for r in Record.Meta.permissions["roles"]],
    )

    submit = SubmitField(_l("Add permissions"))


class EditFileForm(BaseForm):
    """A form for use in editing file metadata.

    :param file: A file used for prefilling the form and checking for duplicate file
        names.
    """

    name = StringField(
        _l("Filename"),
        filters=[normalize],
        validators=[
            DataRequired(),
            Length(max=File.Meta.check_constraints["name"]["length"]["max"]),
        ],
    )

    mimetype = StringField(
        _l("MIME type"),
        filters=[lower, normalize],
        validators=[
            DataRequired(),
            Length(max=File.Meta.check_constraints["mimetype"]["length"]["max"]),
            validate_mimetype,
        ],
    )

    description = LFTextAreaField(
        _l("Description"),
        filters=[empty_str, strip],
        validators=[
            Length(max=File.Meta.check_constraints["description"]["length"]["max"])
        ],
    )

    submit = SubmitField(_l("Save changes"))

    def __init__(self, file, *args, **kwargs):
        self.file = file
        super().__init__(*args, obj=file, **kwargs)

    def validate_name(self, field):
        # pylint: disable=missing-function-docstring
        file = File.query.filter(
            File.record_id == self.file.record_id,
            File.state == FileState.ACTIVE,
            File.name == field.data,
        ).first()

        if file is not None and self.file != file:
            raise StopValidation(_("Name is already in use."))
