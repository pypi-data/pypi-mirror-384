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
from sqlalchemy.dialects.postgresql import JSONB

from kadi.ext.db import db
from kadi.lib.db import SimpleTimestampMixin
from kadi.lib.db import check_constraint
from kadi.lib.db import composite_index
from kadi.lib.db import unique_constraint
from kadi.lib.utils import SimpleReprMixin
from kadi.lib.utils import StringEnum


class Role(SimpleReprMixin, db.Model):
    """Model representing roles.

    A role can be used to determine permissions of a user or group. There are two kinds
    of roles specified by this model:

    * Roles belonging to a specific object instance, in which case the :attr:`object`
      and :attr:`object_id` are set.
    * System roles, possibly belonging to multiple object types and instances, in which
      case the :attr:`object` and :attr:`object_id` are not set.
    """

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "name", "object", "object_id"]
        """See :class:`.SimpleReprMixin`."""

    __tablename__ = "role"

    __table_args__ = (
        unique_constraint(__tablename__, "name", "object", "object_id"),
        check_constraint(
            "(object IS NULL AND object_id IS NULL)"
            " OR (object IS NOT NULL AND object_id IS NOT NULL)",
            "system_role",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the role, auto incremented."""

    name = db.Column(db.Text, nullable=False)
    """The name of the role."""

    object = db.Column(db.Text, nullable=True)
    """The type of object the role refers to.

    If set, always refers to a specific model via its table name. If not set, the
    :attr:`object_id` has to be ``None`` as well.
    """

    object_id = db.Column(db.Integer, nullable=True)
    """The ID of an object the role refers to.

    If not set, the :attr:`object` has to be ``None`` as well.
    """

    users = db.relationship(
        "User", secondary="user_role", lazy="dynamic", back_populates="roles"
    )

    groups = db.relationship(
        "Group", secondary="group_role", lazy="dynamic", back_populates="roles"
    )

    role_rules = db.relationship(
        "RoleRule", back_populates="role", cascade="all, delete-orphan"
    )

    @classmethod
    def create(cls, *, name, object=None, object_id=None):
        """Create a new role and add it to the database session.

        :param name: The name of the role.
        :param object: (optional) The type of object the role refers to.
        :param object_id: (optional) The ID of the object.
        :return: The new :class:`Role` object.
        """
        role = cls(name=name, object=object, object_id=object_id)
        db.session.add(role)

        return role


class RoleRuleType(StringEnum):
    """String enum containing all possible type values for role rules.

    * ``USERNAME``: For rules depending on the username of different user identities.
    """

    __values__ = ["username"]


class RoleRule(SimpleReprMixin, SimpleTimestampMixin, db.Model):
    """Model to represent role rules.

    Role rules can be used to automate permission management by automatically granting
    users or groups roles for different resources based on different conditions.
    """

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "role_id", "type", "condition"]
        """See :class:`.SimpleReprMixin`."""

    __tablename__ = "role_rule"

    __table_args__ = (composite_index(__tablename__, "role_id", "type"),)

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the role rule, auto incremented."""

    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    """The ID of the :class:`.Role` the role rule refers to."""

    type = db.Column(db.Text, nullable=False)
    """The type of the role rule.

    See :class:`.RoleRuleType`.
    """

    condition = db.Column(JSONB, nullable=False)
    """The condition of the role rule, depending on its type.

    For each of the role rule types, the data consists of:

    * ``USERNAME``: An object containing the type of a user's identity
      (``"identity_type"``) and a pattern (``"pattern"``) to check the corresponding
      username with.
    """

    role = db.relationship("Role", back_populates="role_rules")

    @classmethod
    def create(cls, *, role, type, condition):
        """Create a new role rule and add it to the database session.

        :param role: The role the role rule refers to.
        :param type: The type of the role rule.
        :param condition: The condition of the role rule.
        :return: The new :class:`RoleRule` object.
        """
        role_rule = cls(role=role, type=type, condition=condition)
        db.session.add(role_rule)

        return role_rule
