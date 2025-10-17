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
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.api.core import scopes_required
from kadi.lib.api.utils import reqschema
from kadi.lib.api.utils import status
from kadi.lib.permissions.schemas import RoleSchema
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import change_role
from kadi.modules.accounts.models import User
from kadi.modules.collections.core import update_collection
from kadi.modules.collections.models import Collection
from kadi.modules.collections.schemas import CollectionSchema
from kadi.modules.groups.models import Group


@bp.patch("/collections/<int:id>")
@permission_required("update", "collection", "id")
@scopes_required("collection.update")
@reqschema(
    CollectionSchema(exclude=["id"], partial=True),
    description="The new metadata of the collection.",
    bind=False,
)
@status(200, "Return the updated collection.")
@status(409, "A conflict occured while trying to update the collection.")
def edit_collection(id):
    """Update the collection specified by the given ID."""
    collection = Collection.query.get_active_or_404(id)
    data = CollectionSchema(
        previous_collection=collection, exclude=["id"], partial=True
    ).load_or_400()

    if not update_collection(collection, **data):
        return json_error_response(409, description="Error updating collection.")

    return json_response(200, CollectionSchema().dump(collection))


@bp.patch("/collections/<int:collection_id>/roles/users/<int:user_id>")
@permission_required("permissions", "collection", "collection_id")
@scopes_required("collection.permissions")
@reqschema(RoleSchema, description="The new user role.")
@status(204, "User role successfully changed.")
@status(
    409,
    "When trying to change the creator's role or a conflict occured while trying to"
    " change the role.",
)
def change_collection_user_role(collection_id, user_id, schema):
    """Change a user role of a collection.

    Will change the role of the user specified by the given user ID of the collection
    specified by the given collection ID.
    """
    collection = Collection.query.get_active_or_404(collection_id)
    user = User.query.get_active_or_404(user_id)

    if user.is_merged:
        return json_error_response(404)

    return change_role(user, collection, schema.load_or_400()["name"])


@bp.patch("/collections/<int:collection_id>/roles/groups/<int:group_id>")
@permission_required("permissions", "collection", "collection_id")
@scopes_required("collection.permissions")
@reqschema(RoleSchema, description="The new group role.")
@status(204, "Group role successfully changed.")
@status(409, "A conflict occured while trying to change the role.")
def change_collection_group_role(collection_id, group_id, schema):
    """Change a group role of a collection.

    Will change the role of the group specified by the given group ID of the collection
    specified by the given collection ID.
    """
    collection = Collection.query.get_active_or_404(collection_id)
    group = Group.query.get_active_or_404(group_id)

    return change_role(group, collection, schema.load_or_400()["name"])
