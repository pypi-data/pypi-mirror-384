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
from functools import wraps

from flask import abort
from flask import current_app
from flask_login import current_user
from flask_login import login_required

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import get_class_by_tablename
from kadi.lib.utils import rgetattr
from kadi.modules.accounts.models import User
from kadi.modules.accounts.models import UserState
from kadi.modules.groups.models import Group
from kadi.modules.groups.models import GroupState

from .core import create_role_rule
from .core import has_permission
from .models import Role
from .models import RoleRule
from .models import RoleRuleType


def permission_required(action, object_name, object_id_identifier, status_code=403):
    """Decorator to add access restrictions based on permissions to an endpoint.

    If the current user is not authenticated, the decorator will behave the same as
    Flask-Login's ``login_required`` decorator. If the object or object instance to
    check do not exist, the request will automatically get aborted with a 404 status
    code.

    Uses :func:`kadi.lib.permissions.core.has_permission` to check for access
    permissions.

    :param action: See :func:`kadi.lib.permissions.core.has_permission`.
    :param object_name: See :func:`kadi.lib.permissions.core.has_permission`.
    :param object_id_identifier: The name of the variable to use as ``object_id``, which
        needs to be part of the keyword arguments of the decorated function. May also be
        ``None``.
    :param status_code: (optional) The status code to use if no permission was granted.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            object_id = None

            if object_id_identifier is not None:
                object_id = kwargs[object_id_identifier]

            model = get_class_by_tablename(object_name)

            # Always return 404 if the model or object do not exist.
            if model is None or (
                object_id is not None
                and not model.query.filter_by(id=object_id)
                .with_entities(model.id)
                .first()
            ):
                abort(404)

            if not has_permission(current_user, action, object_name, object_id):
                abort(status_code)

            return func(*args, **kwargs)

        return login_required(wrapper)

    return decorator


def initialize_roles(object_name, object_id):
    """Initialize all roles of a specific object.

    Will create database objects of the roles specified in the ``Meta.permissions``
    attribute in the model corresponding to the given object type.

    **Example:**

    .. code-block:: python3

        class Foo:
            class Meta:
                permissions = {
                    "roles": {
                        "admin": ["read", "update"],
                    },
                }

    :param object_name: The type of object the roles refer to.
    :param object_id: The ID of the object.
    :raises ValueError: If no object with the given arguments exists.
    """
    model = get_class_by_tablename(object_name)

    if model is None:
        raise ValueError(f"Object type '{object_name}' does not exist.")

    object_instance = model.query.get(object_id)

    if object_instance is None:
        raise ValueError(f"Object '{object_name}' with ID {object_id} does not exist.")

    for role_name in model.Meta.permissions["roles"]:
        Role.create(name=role_name, object=object_name, object_id=object_id)


def delete_roles(object_name, object_id):
    """Delete the roles of a specific object.

    :param object_name: The type of object the roles refer to.
    :param object_id: The ID of the object.
    """
    roles_query = Role.query.filter(
        Role.object == object_name, Role.object_id == object_id
    )

    for role in roles_query:
        db.session.delete(role)


def get_user_roles(object_name, object_id=None):
    """Get all users and roles of a specific object or object type.

    Note that inactive users will be filtered out.

    :param object_name: The type of the object.
    :param object_id: (optional) The ID of a specific object.
    :return: The users and corresponding roles of the object(s) as query.
    """
    user_roles_query = (
        db.session.query(User, Role)
        .join(User.roles)
        .filter(Role.object == object_name, User.state == UserState.ACTIVE)
    )

    if object_id:
        user_roles_query = user_roles_query.filter(Role.object_id == object_id)

    return user_roles_query


def get_group_roles(object_name, object_id=None):
    """Get all groups and roles of a specific object or object type.

    Note that inactive groups will be filtered out.

    :param object_name: The type of the object.
    :param object_id: (optional) The ID of a specific object.
    :return: The groups and corresponding roles of the object(s) as query.
    """
    group_roles_query = (
        db.session.query(Group, Role)
        .join(Group.roles)
        .filter(Role.object == object_name, Group.state == GroupState.ACTIVE)
    )

    if object_id:
        group_roles_query = group_roles_query.filter(Role.object_id == object_id)

    return group_roles_query


def get_object_roles(object_name):
    """Get all available roles and corresponding permissions of an object type.

    :param object_name: The type of the object.
    :return: A list of dictionaries in the following form:

        .. code-block:: python3

            [
                {
                    "name": "admin",
                    "permissions": [
                        {
                            "action": "read,
                            "description": "Read this resource.",
                        }
                    ]
                }
            ]
    """
    model = get_class_by_tablename(object_name)
    permissions_meta = rgetattr(model, "Meta.permissions", {})

    object_roles = []

    for role_name, actions in permissions_meta.get("roles", {}).items():
        role_permissions = []
        object_roles.append(
            {
                "name": role_name,
                "permissions": role_permissions,
            }
        )

        for action in actions:
            role_permissions.append(
                {
                    "action": action,
                    "description": permissions_meta["actions"][action],
                }
            )

    return object_roles


def initialize_system_roles():
    """Initialize all system roles.

    Will create database objects of the system roles defined in
    :const:`kadi.lib.constants.SYSTEM_ROLES` that do not exist yet.

    :return: ``True`` if at least one system role was created, ``False`` otherwise.
    """
    role_created = False

    for role_name in const.SYSTEM_ROLES:
        if (
            Role.query.filter_by(name=role_name, object=None, object_id=None).first()
            is None
        ):
            Role.create(name=role_name)
            role_created = True

    return role_created


def create_username_role_rule(
    object_name, object_id, role_name, identity_type, pattern
):
    """Create a role rule with conditions to check the values of usernames.

    The conditions of username rules consist of an identity type (``identity_type``) and
    a pattern (``pattern``). The former specifies the type of identities to check the
    usernames of, while the letter specifies the possible values of the usernames. The
    pattern may include one or more wildcards using ``"*"``, which match a sequence of
    zero or more characters.

    :param object_name: See :func:`kadi.lib.permissions.core.create_role_rule`.
    :param object_id: See :func:`kadi.lib.permissions.core.create_role_rule`.
    :param role_name: See :func:`kadi.lib.permissions.core.create_role_rule`.
    :param identity_type: The identity type of the condition.
    :param pattern: The pattern expression of the condition.
    :return: See :func:`kadi.lib.permissions.core.create_role_rule`.
    """
    if identity_type not in current_app.config["AUTH_PROVIDERS"]:
        return None

    condition = {"identity_type": identity_type, "pattern": str(pattern)}
    return create_role_rule(
        object_name, object_id, role_name, RoleRuleType.USERNAME, condition
    )


def get_role_rules(object_name, object_id, rule_type=None):
    """Get all existing role rules corresponding to roles of a specific object.

    :param object_name: The type of object the role rules refer to through their
        corresponding roles.
    :param object_id: The ID of the object the role rules refer to through their
        corresponding roles.
    :param rule_type: (optional) A type to limit the role rules with.
    :return: The filtered role rules as query.
    """
    role_ids_query = Role.query.filter(
        Role.object == object_name, Role.object_id == object_id
    ).with_entities(Role.id)

    role_rule_query = RoleRule.query.filter(RoleRule.role_id.in_(role_ids_query))

    if rule_type is not None:
        role_rule_query = role_rule_query.filter(RoleRule.type == rule_type)

    return role_rule_query
