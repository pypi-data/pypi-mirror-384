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
from flask_babel import lazy_gettext as _l

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import StateTimestampMixin
from kadi.lib.db import generate_check_constraints
from kadi.lib.favorites.models import FavoriteMixin
from kadi.lib.search.models import SearchableMixin
from kadi.lib.tags.models import TaggingMixin
from kadi.lib.utils import SimpleReprMixin
from kadi.lib.utils import StringEnum


class CollectionVisibility(StringEnum):
    """String enum containing all possible visibility values for collections.

    * ``PRIVATE``: For collections that are not readable without explicit permission.
    * ``PUBLIC``: For collections that are readable by all authenticated users.
    """

    __values__ = [const.RESOURCE_VISIBILITY_PRIVATE, const.RESOURCE_VISIBILITY_PUBLIC]


class CollectionState(StringEnum):
    """String enum containing all possible state values for collections.

    * ``ACTIVE``: For collections that are active.
    * ``DELETED``: For collections that have been marked for deletion.
    """

    __values__ = [const.MODEL_STATE_ACTIVE, const.MODEL_STATE_DELETED]


class Collection(
    SimpleReprMixin,
    SearchableMixin,
    StateTimestampMixin,
    FavoriteMixin,
    TaggingMixin,
    db.Model,
):
    """Model to represent collections."""

    class Meta:
        """Container to store meta class attributes."""

        representation = [
            "id",
            "user_id",
            "parent_id",
            "identifier",
            "visibility",
            "state",
        ]
        """See :class:`.SimpleReprMixin`."""

        search_mapping = "kadi.modules.collections.mappings.CollectionMapping"
        """See :class:`.SearchableMixin`."""

        revision = [
            "identifier",
            "title",
            "description",
            "visibility",
            "state",
            "tags[name]",
            "record_template[id]",
        ]
        """See :func:`kadi.lib.revisions.core.setup_revisions`."""

        permissions = {
            "actions": {
                "create": "Create new collections.",
                "read": _l("View this collection."),
                "link": _l("Manage links of this collection with other resources."),
                "update": _l("Edit this collection."),
                "permissions": _l("Manage permissions of this collection."),
                "delete": _l("Delete this collection."),
            },
            "roles": {
                "member": ["read"],
                "collaborator": ["read", "link"],
                "editor": ["read", "link", "update"],
                "admin": ["read", "link", "update", "permissions", "delete"],
            },
            "default_permissions": {
                "read": {"visibility": CollectionVisibility.PUBLIC},
            },
        }
        """Available actions, roles and default permissions for collections.

        See :mod:`kadi.lib.permissions`.
        """

        check_constraints = {
            "identifier": {"length": {"max": const.RESOURCE_IDENTIFIER_MAX_LEN}},
            "title": {"length": {"max": const.RESOURCE_TITLE_MAX_LEN}},
            "description": {"length": {"max": const.RESOURCE_DESCRIPTION_MAX_LEN}},
            "visibility": {"values": CollectionVisibility.__values__},
            "state": {"values": CollectionState.__values__},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "collection"

    __table_args__ = generate_check_constraints(Meta.check_constraints)

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the collection, auto incremented."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` who created the collection."""

    parent_id = db.Column(db.Integer, db.ForeignKey("collection.id"), nullable=True)
    """The optional ID of the parent :class:`.Collection`."""

    identifier = db.Column(db.Text, index=True, unique=True, nullable=False)
    """The unique identifier of the collection.

    Restricted to a maximum length of ``50`` characters.
    """

    title = db.Column(db.Text, nullable=False)
    """The title of the collection.

    Restricted to a maximum length of ``150`` characters.
    """

    description = db.Column(db.Text, nullable=False)
    """The description of the collection.

    Restricted to a maximum length of ``50_000`` characters.
    """

    plain_description = db.Column(db.Text, nullable=False)
    """The plain description of the collection.

    Equal to the normal description with the difference that most markdown is stripped
    out and whitespaces are normalized.
    """

    visibility = db.Column(db.Text, index=True, nullable=False)
    """The default visibility of the collection.

    See :class:`.CollectionVisibility`.
    """

    record_template_id = db.Column(
        db.Integer, db.ForeignKey("template.id"), nullable=True
    )
    """The optional ID of a record :class:`.Template` associated with the collection.

    If specified, the template will be used as a default when adding new records to the
    collection.
    """

    state = db.Column(db.Text, index=True, nullable=False)
    """The state of the collection.

    See :class:`.CollectionState`.
    """

    creator = db.relationship("User", back_populates="collections")

    parent = db.relationship(
        "Collection",
        remote_side="Collection.id",
        backref=db.backref("children", lazy="dynamic"),
    )

    record_template = db.relationship("Template", back_populates="collections")

    records = db.relationship(
        "Record",
        secondary="record_collection",
        lazy="dynamic",
        back_populates="collections",
    )

    tags = db.relationship(
        "Tag", secondary="collection_tag", lazy="dynamic", back_populates="collections"
    )

    @classmethod
    def create(
        cls,
        *,
        creator,
        identifier,
        title,
        description="",
        plain_description="",
        visibility=CollectionVisibility.PRIVATE,
        record_template=None,
        state=CollectionState.ACTIVE,
    ):
        """Create a new collection and add it to the database session.

        :param creator: The creator of the collection.
        :param identifier: The unique identifier of the collection.
        :param title: The title of the collection.
        :param description: (optional) The description of the collection.
        :param plain_description: (optional) The plain description of the collection.
        :param visibility: (optional) The default visibility of the collection.
        :param record_template: (optional) The record template of the collection.
        :param state: (optional) The state of the collection.
        :return: The new :class:`Collection` object.
        """
        collection = cls(
            creator=creator,
            identifier=identifier,
            title=title,
            description=description,
            plain_description=plain_description,
            visibility=visibility,
            record_template=record_template,
            state=state,
        )
        db.session.add(collection)

        return collection


# Auxiliary table for collection tags.
db.Table(
    "collection_tag",
    db.Column(
        "collection_id", db.Integer, db.ForeignKey("collection.id"), primary_key=True
    ),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)
