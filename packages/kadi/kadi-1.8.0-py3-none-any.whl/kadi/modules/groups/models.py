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
from sqlalchemy.dialects.postgresql import UUID

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import StateTimestampMixin
from kadi.lib.db import generate_check_constraints
from kadi.lib.favorites.models import FavoriteMixin
from kadi.lib.search.models import SearchableMixin
from kadi.lib.utils import SimpleReprMixin
from kadi.lib.utils import StringEnum


class GroupVisibility(StringEnum):
    """String enum containing all possible visibility values for groups.

    * ``PRIVATE``: For groups that are not readable without explicit permission.
    * ``PUBLIC``: For groups that are readable by all authenticated users.
    """

    __values__ = [const.RESOURCE_VISIBILITY_PRIVATE, const.RESOURCE_VISIBILITY_PUBLIC]


class GroupState(StringEnum):
    """String enum containing all possible state values for groups.

    * ``ACTIVE``: For groups that are active.
    * ``DELETED``: For groups that have been marked for deletion.
    """

    __values__ = [const.MODEL_STATE_ACTIVE, const.MODEL_STATE_DELETED]


class Group(
    SimpleReprMixin, SearchableMixin, StateTimestampMixin, FavoriteMixin, db.Model
):
    """Model to represent groups."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "identifier", "visibility", "state"]
        """See :class:`.SimpleReprMixin`."""

        search_mapping = "kadi.modules.groups.mappings.GroupMapping"
        """See :class:`.SearchableMixin`."""

        timestamp_exclude = ["roles"]
        """See :class:`.BaseTimestampMixin`."""

        revision = ["identifier", "title", "description", "visibility", "state"]
        """See :func:`kadi.lib.revisions.core.setup_revisions`."""

        permissions = {
            "actions": {
                "create": "Create new groups.",
                "read": _l("View this group."),
                "update": _l("Edit this group."),
                "members": _l("Manage members of this group."),
                "delete": _l("Delete this group."),
            },
            "roles": {
                "member": ["read"],
                "editor": ["read", "update"],
                "admin": ["read", "update", "members", "delete"],
            },
            "default_permissions": {
                "read": {"visibility": GroupVisibility.PUBLIC},
            },
        }
        """Available actions, roles and default permissions for groups.

        See :mod:`kadi.lib.permissions`.
        """

        check_constraints = {
            "identifier": {"length": {"max": const.RESOURCE_IDENTIFIER_MAX_LEN}},
            "title": {"length": {"max": const.RESOURCE_TITLE_MAX_LEN}},
            "description": {"length": {"max": const.RESOURCE_DESCRIPTION_MAX_LEN}},
            "visibility": {"values": GroupVisibility.__values__},
            "state": {"values": GroupState.__values__},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "group"

    __table_args__ = generate_check_constraints(Meta.check_constraints)

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the group, auto incremented."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` who created the group."""

    identifier = db.Column(db.Text, index=True, unique=True, nullable=False)
    """The unique identifier of the group.

    Restricted to a maximum length of ``50`` characters.
    """

    title = db.Column(db.Text, nullable=False)
    """The title of the group.

    Restricted to a maximum length of ``150`` characters.
    """

    description = db.Column(db.Text, nullable=False)
    """The description of the group.

    Restricted to a maximum length of ``50_000`` characters.
    """

    plain_description = db.Column(db.Text, nullable=False)
    """The plain description of the group.

    Equal to the normal description with the difference that most markdown is stripped
    out and whitespaces are normalized.
    """

    image_name = db.Column(UUID(as_uuid=True), nullable=True)
    """The optional identifier of a group's profile image."""

    visibility = db.Column(db.Text, index=True, nullable=False)
    """The default visibility of the group.

    See :class:`.GroupVisibility`.
    """

    state = db.Column(db.Text, index=True, nullable=False)
    """The state of the group.

    See :class:`.GroupState`.
    """

    creator = db.relationship("User", back_populates="groups")

    roles = db.relationship(
        "Role", secondary="group_role", lazy="dynamic", back_populates="groups"
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
        visibility=GroupVisibility.PRIVATE,
        state=GroupState.ACTIVE,
    ):
        """Create a new group and add it to the database session.

        :param creator: The creator of the group.
        :param identifier: The unique identifier of the group.
        :param title: The title of the group.
        :param description: (optional) The description of the group.
        :param plain_description: (optional) The plain description of the group.
        :param visibility: (optional) The default visibility of the group.
        :param state: (optional) The state of the group.
        :return: The new :class:`Group` object.
        """
        group = cls(
            creator=creator,
            identifier=identifier,
            title=title,
            description=description,
            plain_description=plain_description,
            visibility=visibility,
            state=state,
        )
        db.session.add(group)

        return group


# Auxiliary table for group roles.
db.Table(
    "group_role",
    db.Column("group_id", db.Integer, db.ForeignKey("group.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id"), primary_key=True),
)
