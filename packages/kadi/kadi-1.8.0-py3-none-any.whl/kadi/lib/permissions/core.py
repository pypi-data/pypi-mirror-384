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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.cache import memoize_request
from kadi.lib.db import BaseTimestampMixin
from kadi.lib.db import NestedTransaction
from kadi.lib.db import escape_like
from kadi.lib.db import get_class_by_tablename
from kadi.lib.utils import rgetattr
from kadi.modules.accounts.models import User
from kadi.modules.groups.models import Group

from .models import Role
from .models import RoleRule
from .models import RoleRuleType


def _get_base_roles_query(subject, check_groups):
    from kadi.modules.groups.utils import get_user_groups

    roles_query = subject.roles

    if isinstance(subject, User) and check_groups:
        group_ids_query = get_user_groups(subject).with_entities(Group.id)
        roles_query = roles_query.union(
            Role.query.join(Role.groups).filter(Group.id.in_(group_ids_query))
        )

    return roles_query


def _get_valid_system_roles(action, object_name):
    valid_system_roles = []

    for system_role_name, system_role_meta in const.SYSTEM_ROLES.items():
        actions = system_role_meta.get(object_name, [])

        if action in actions:
            valid_system_roles.append(system_role_name)

    return valid_system_roles


@memoize_request
def has_permission(
    subject, action, object_name, object_id, check_groups=True, check_defaults=True
):
    """Check if a user or group has permission to perform a specific action.

    Checks all permissions corresponding to the roles of the given subject.

    Supports memoization via :func:`kadi.lib.cache.memoize_request`.

    :param subject: The :class:`.User` or :class:`.Group`.
    :param action: The action to check for.
    :param object_name: The type of object.
    :param object_id: The ID of a specific object or ``None`` for a global permission.
    :param check_groups: (optional) Flag indicating whether the groups of a user should
        be checked as well for their permissions.
    :param check_defaults: (optional) Flag indicating whether the default permissions of
        any object should be checked as well.
    :return: ``True`` if permission is granted, ``False`` otherwise or if the object
        instance to check does not exist.
    """
    model = get_class_by_tablename(object_name)

    if model is None:
        return False

    base_roles_query = _get_base_roles_query(subject, check_groups)

    # Check the system roles.
    valid_system_roles = _get_valid_system_roles(action, object_name)
    system_roles_query = base_roles_query.filter(
        Role.name.in_(valid_system_roles),
        Role.object.is_(None),
        Role.object_id.is_(None),
    )

    if system_roles_query.with_entities(Role.id).first() is not None:
        return True

    if object_id is None:
        return False

    object_instance = model.query.get(object_id)

    if object_instance is None:
        return False

    permissions_meta = rgetattr(model, "Meta.permissions", {})

    # Check the default permissions, if applicable.
    if check_defaults:
        default_permissions = permissions_meta.get("default_permissions", {})

        for attr, val in default_permissions.get(action, {}).items():
            if getattr(object_instance, attr) == val:
                return True

    # Finally, check the regular roles.
    valid_roles = []

    for role_name, actions in permissions_meta.get("roles", {}).items():
        if action in actions:
            valid_roles.append(role_name)

    regular_roles_query = base_roles_query.filter(
        Role.name.in_(valid_roles),
        Role.object == object_name,
        Role.object_id == object_id,
    )

    return regular_roles_query.with_entities(Role.id).first() is not None


def get_permitted_objects(
    subject, action, object_name, check_groups=True, check_defaults=True
):
    """Get all objects a user or group has a specific permission for.

    Checks all permissions corresponding to the roles of the given subject.

    :param subject: The :class:`.User` or :class:`.Group`.
    :param action: The action to check for.
    :param object_name: The type of object.
    :param check_groups: (optional) Flag indicating whether the groups of a user should
        be checked as well for their permissions.
    :param check_defaults: (optional) Flag indicating whether the default permissions of
        the objects should be checked as well.
    :return: The permitted objects as query or ``None`` if the object type does not
        exist.
    """
    model = get_class_by_tablename(object_name)

    if model is None:
        return None

    base_roles_query = _get_base_roles_query(subject, check_groups)

    # Check the system roles.
    valid_system_roles = _get_valid_system_roles(action, object_name)
    system_roles_query = base_roles_query.filter(
        Role.name.in_(valid_system_roles),
        Role.object.is_(None),
        Role.object_id.is_(None),
    )

    if system_roles_query.with_entities(Role.id).first() is not None:
        return model.query

    permissions_meta = rgetattr(model, "Meta.permissions", {})

    # Get all objects for the regular permissions.
    valid_roles = []

    for role_name, actions in permissions_meta.get("roles", {}).items():
        if action in actions:
            valid_roles.append(role_name)

    regular_roles_query = base_roles_query.filter(
        Role.name.in_(valid_roles), Role.object == object_name
    )
    objects_query = model.query.filter(
        model.id.in_(regular_roles_query.with_entities(Role.object_id))
    )

    # Include all objects for the default permissions, if applicable.
    if check_defaults:
        default_permissions = permissions_meta.get("default_permissions", {})
        filters = []

        for attr, val in default_permissions.get(action, {}).items():
            filters.append(getattr(model, attr) == val)

        if filters:
            return objects_query.union(model.query.filter(db.or_(*filters)))

    return objects_query


def add_role(subject, object_name, object_id, role_name, update_timestamp=True):
    """Add an existing role to a user or group.

    :param subject: The :class:`.User` or :class:`.Group`.
    :param object_name: The type of object the role refers to.
    :param object_id: The ID of the object.
    :param role_name: The name of the role.
    :param update_timestamp: (optional) Flag indicating whether the timestamp of the
        underlying object should be updated or not. The object needs to implement
        :class:`.BaseTimestampMixin` in that case.
    :return: ``True`` if the role was added successfully, ``False`` if the subject
        already has a role related to the given object.
    :raises ValueError: If no object or role with the given arguments exists or when
        trying to add a role to the object that is being referred to by that role.
    """
    model = get_class_by_tablename(object_name)

    if model is None:
        raise ValueError(f"Object type '{object_name}' does not exist.")

    object_instance = model.query.get(object_id)

    if object_instance is None:
        raise ValueError(f"Object '{object_name}' with ID {object_id} does not exist.")

    if subject.__tablename__ == object_name and subject.id == object_id:
        raise ValueError("Cannot add a role to the object to which the role refers.")

    roles = subject.roles.filter(
        Role.object == object_name, Role.object_id == object_id
    )

    if roles.count() > 0:
        return False

    role = Role.query.filter_by(
        name=role_name, object=object_name, object_id=object_id
    ).first()

    if not role:
        raise ValueError("A role with that name does not exist.")

    with NestedTransaction(exc=IntegrityError) as t:
        subject.roles.append(role)

    if (
        t.success
        and update_timestamp
        and isinstance(object_instance, BaseTimestampMixin)
    ):
        object_instance.update_timestamp()

    return t.success


def remove_role(subject, object_name, object_id, update_timestamp=True):
    """Remove an existing role of a user or group.

    :param subject: The :class:`.User` or :class:`.Group`.
    :param object_name: The type of object the role refers to.
    :param object_id: The ID of the object.
    :param update_timestamp: (optional) Flag indicating whether the timestamp of the
        underlying object should be updated or not. The object needs to implement
        :class:`.BaseTimestampMixin` in that case.
    :return: ``True`` if the role was removed successfully, ``False`` if there was no
        role to remove.
    :raises ValueError: If no object with the given arguments exists.
    """
    model = get_class_by_tablename(object_name)

    if model is None:
        raise ValueError(f"Object type '{object_name}' does not exist.")

    object_instance = model.query.get(object_id)

    if object_instance is None:
        raise ValueError(f"Object '{object_name}' with ID {object_id} does not exist.")

    roles = subject.roles.filter(
        Role.object == object_name, Role.object_id == object_id
    )

    if roles.count() == 0:
        return False

    with NestedTransaction(exc=StaleDataError) as t:
        # As in certain circumstances (e.g. merging two users or potential race
        # conditions when adding roles) a subject may have multiple different roles, all
        # roles related to the given object will be removed.
        for role in roles:
            subject.roles.remove(role)

    if (
        t.success
        and update_timestamp
        and isinstance(object_instance, BaseTimestampMixin)
    ):
        object_instance.update_timestamp()

    return t.success


def set_system_role(user, system_role):
    """Set an existing system role for a given user.

    :param user: The user to set the system role for.
    :param system_role: The name of the system role to set as defined in
        :const:`kadi.lib.constants.SYSTEM_ROLES`.
    :return: ``True`` if the system role was set successfully, ``False`` otherwise or if
        the given system role does not exist.
    """
    new_role = Role.query.filter_by(
        name=system_role, object=None, object_id=None
    ).first()

    if new_role is None:
        return False

    user_roles = user.roles.filter(Role.object.is_(None), Role.object_id.is_(None))

    with NestedTransaction(exc=StaleDataError) as t:
        # As in certain circumstances (e.g. merging two users) a user may have different
        # system roles, all of them will be removed.
        for role in user_roles:
            user.roles.remove(role)

    if not t.success:
        return False

    with NestedTransaction(exc=IntegrityError) as t:
        user.roles.append(new_role)

    return t.success


def create_role_rule(
    object_name, object_id, role_name, rule_type, condition, update_timestamp=True
):
    """Create a new role rule.

    :param object_name: The type of object the role refers to.
    :param object_id: The ID of the object.
    :param role_name: The name of the role.
    :param rule_type: The type of the role rule.
    :param condition: The condition of the role rule.
    :param update_timestamp: (optional) Flag indicating whether the timestamp of the
        underlying object should be updated or not. The object needs to implement
        :class:`.BaseTimestampMixin` in that case.
    :return: The created role rule or ``None`` if the role rule could not be created.
    """
    model = get_class_by_tablename(object_name)

    if model is None:
        return None

    object_instance = model.query.get(object_id)

    if object_instance is None:
        return None

    # Basic structure check of the condition data.
    if rule_type == RoleRuleType.USERNAME and not isinstance(condition, dict):
        return None

    role = Role.query.filter_by(
        name=role_name, object=object_name, object_id=object_id
    ).first()

    if not role:
        return None

    if update_timestamp and isinstance(object_instance, BaseTimestampMixin):
        object_instance.update_timestamp()

    return RoleRule.create(role=role, type=rule_type, condition=condition)


def remove_role_rule(role_rule, update_timestamp=True):
    """Remove an existing role rule.

    :param role_role: The role rule to remove.
    :param update_timestamp: (optional) Flag indicating whether the timestamp of the
        underlying object should be updated or not. The object needs to implement
        :class:`.BaseTimestampMixin` in that case.
    """
    role = role_rule.role

    model = get_class_by_tablename(role.object)
    object_instance = model.query.get(role.object_id)

    if update_timestamp and isinstance(object_instance, BaseTimestampMixin):
        object_instance.update_timestamp()

    db.session.delete(role_rule)


def apply_role_rule(role_rule, user=None):
    """Apply a given role rule.

    :param role_rule: The role rule to apply.
    :param user: (optional) A specific user to apply the role rule to. If not given, all
        existing users are considered.
    """
    role = role_rule.role

    if role_rule.type == RoleRuleType.USERNAME:
        identity_type = role_rule.condition.get("identity_type")
        provider_config = current_app.config["AUTH_PROVIDERS"].get(identity_type)

        if provider_config is None:
            return

        pattern = role_rule.condition.get("pattern", "")
        # As the pattern is used in a LIKE query, escape it first and then replace all
        # wildcards (*) with the ones used by the database (%).
        pattern = escape_like(pattern).replace("*", "%")

        identity_class = provider_config["identity_class"]
        identities_query = identity_class.query.filter(
            identity_class.username.like(pattern)
        )

        if user is not None:
            # The role only needs to be added once, even if a user has multiple matching
            # identities.
            identity = identities_query.filter(
                identity_class.user_id == user.id
            ).first()

            if identity is not None:
                add_role(identity.user, role.object, role.object_id, role.name)
        else:
            for identity in identities_query:
                add_role(identity.user, role.object, role.object_id, role.name)
