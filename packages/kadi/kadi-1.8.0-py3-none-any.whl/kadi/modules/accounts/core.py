# Copyright 2021 Karlsruhe Institute of Technology
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
from sqlalchemy.inspection import inspect

from kadi.ext.db import db
from kadi.lib.db import get_class_by_tablename
from kadi.lib.db import is_many_relationship
from kadi.lib.permissions.core import add_role
from kadi.lib.permissions.core import remove_role
from kadi.lib.permissions.core import set_system_role
from kadi.lib.permissions.models import Role
from kadi.modules.collections.core import purge_collection
from kadi.modules.groups.core import purge_group
from kadi.modules.records.core import purge_record
from kadi.modules.templates.core import purge_template

from .models import User
from .utils import delete_user_image


def _purge_merged_users(user):
    for merged_user in User.query.filter(User.new_user_id == user.id):
        _purge_merged_users(merged_user)

        db.session.delete(merged_user)
        db.session.commit()


def purge_user(user):
    """Purge an existing user.

    This will completely delete the user and all their resources from the database.

    Note that this function issues one or more database commits.

    :param user: The user to purge.
    """
    delete_user_image(user)

    for record in user.records:
        purge_record(record)

    for collection in user.collections:
        purge_collection(collection)

    for template in user.templates:
        purge_template(template)

    for group in user.groups:
        purge_group(group)

    # We need to remove the reference to the latest identity separately because of the
    # cyclic user/identity reference.
    user.identity = None
    db.session.commit()

    # Also delete all users that may have been merged into the user to delete
    # recursively. These users should not be referenced anywhere anymore.
    _purge_merged_users(user)

    db.session.delete(user)
    db.session.commit()


def merge_users(primary_user, secondary_user):
    """Merge two users together.

    This will migrate the ownership of all identities, resources and roles from the
    secondary user to the primary user. The primary user will then be able to log in
    using both identities.

    :param primary_user: The primary user to merge the secondary user into.
    :param secondary_user: The secondary user to merge into the primary user.
    """
    if primary_user == secondary_user:
        return

    primary_system_role = primary_user.roles.filter(
        Role.object.is_(None), Role.object_id.is_(None)
    ).first()

    # Migrate all roles. Note that in case both users have different roles for the same
    # resource, the primary user will end up with multiple roles. However, this does not
    # really matter for permission handling and would resolve itself once a role is
    # changed again. A special case is the creator's role, which cannot be changed, so
    # we handle this case separately.
    for role in secondary_user.roles:
        if role.object is not None:
            model = get_class_by_tablename(role.object)
            object_instance = model.query.get(role.object_id)

            if object_instance is None:
                continue

            # If any of the two users is the creator of the resource corresponding to
            # the current role, make sure that the primary user only has one single
            # "admin" role.
            if object_instance.creator in {primary_user, secondary_user}:
                role_args = [primary_user, role.object, role.object_id]
                remove_role(*role_args, update_timestamp=False)
                add_role(*role_args, "admin", update_timestamp=False)
                continue

        if role not in primary_user.roles:
            primary_user.roles.append(role)

    secondary_user.roles = []

    # Make sure the primary user only has the system role they already had before.
    set_system_role(primary_user, primary_system_role.name)

    # Migrate favorited resources.
    for favorite in secondary_user.favorites:
        if (
            primary_user.favorites.filter_by(
                object=favorite.object, object_id=favorite.object_id
            ).first()
            is None
        ):
            favorite.user = primary_user

    secondary_user.favorites = []

    # Migrate config items.
    for config_item in secondary_user.config_items:
        if primary_user.config_items.filter_by(key=config_item.key).first() is None:
            config_item.user = primary_user

    secondary_user.config_items = []

    # Migrate OAuth2 client tokens.
    for oauth2_client_token in secondary_user.oauth2_client_tokens:
        if (
            primary_user.oauth2_client_tokens.filter_by(
                name=oauth2_client_token.name
            ).first()
            is not None
        ):
            oauth2_client_token.user = primary_user

    secondary_user.oauth2_client_tokens = []

    # Migrate OAuth2 server tokens.
    for oauth2_server_token in secondary_user.oauth2_server_tokens:
        if (
            primary_user.oauth2_server_tokens.filter_by(
                client_id=oauth2_server_token.client_id
            ).first()
            is not None
        ):
            oauth2_server_token.user = primary_user

    secondary_user.oauth2_server_tokens = []

    # Migrate all remaining many-relationships.
    for relationship in inspect(User).relationships.keys():
        if is_many_relationship(User, relationship) and relationship not in {
            "roles",
            "favorites",
            "config_items",
            "oauth2_client_tokens",
            "oauth2_server_tokens",
        }:
            # Note that this way of updating won't trigger the automatic timestamp
            # updates.
            getattr(secondary_user, relationship).update({"user_id": primary_user.id})

    # Delete the profile image of the secondary user.
    delete_user_image(secondary_user)

    # Finally, remove the reference of the secondary user's latest identity and set the
    # ID of the primary user as the secondary user's new user ID, marking the secondary
    # user as merged.
    secondary_user.identity = None
    secondary_user.new_user_id = primary_user.id
