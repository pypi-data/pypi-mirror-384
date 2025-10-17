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
from flask_login import current_user
from flask_login import login_required

from kadi.ext.db import db
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.api.core import scopes_required
from kadi.lib.api.utils import reqschema
from kadi.lib.api.utils import status
from kadi.lib.exceptions import KadiPermissionError
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import add_link
from kadi.lib.resources.api import add_role
from kadi.lib.resources.schemas import GroupResourceRoleSchema
from kadi.lib.resources.schemas import UserResourceRoleSchema
from kadi.modules.accounts.models import User
from kadi.modules.collections.core import create_collection
from kadi.modules.collections.core import link_collections
from kadi.modules.collections.core import purge_collection as _purge_collection
from kadi.modules.collections.core import restore_collection as _restore_collection
from kadi.modules.collections.models import Collection
from kadi.modules.collections.models import CollectionState
from kadi.modules.collections.schemas import CollectionSchema
from kadi.modules.groups.models import Group
from kadi.modules.records.models import Record
from kadi.modules.records.schemas import RecordSchema


@bp.post("/collections")
@permission_required("create", "collection", None)
@scopes_required("collection.create")
@reqschema(
    CollectionSchema(exclude=["id"]), description="The metadata of the new collection."
)
@status(201, "Return the new collection.")
@status(409, "A conflict occured while trying to create the collection.")
def new_collection(schema):
    """Create a new collection."""
    collection = create_collection(**schema.load_or_400())

    if not collection:
        return json_error_response(409, description="Error creating collection.")

    return json_response(201, CollectionSchema().dump(collection))


@bp.post("/collections/<int:id>/records")
@permission_required("link", "collection", "id")
@scopes_required("collection.link")
@reqschema(
    RecordSchema(only=["id"]), description="The record to add to the collection."
)
@status(201, "Record successfully added to collection.")
@status(409, "The link already exists.")
def add_collection_record(id, schema):
    """Add a record to the collection specified by the given ID."""
    collection = Collection.query.get_active_or_404(id)
    record = Record.query.get_active_or_404(schema.load_or_400()["id"])

    return add_link(collection.records, record)


@bp.post("/collections/<int:id>/collections")
@permission_required("link", "collection", "id")
@scopes_required("collection.link")
@reqschema(
    CollectionSchema(only=["id"]),
    description="The child collection to add to the collection.",
)
@status(201, "Child collection successfully added to collection.")
@status(
    409,
    "When trying to link the collection with itself, the child collection already has a"
    " parent or it is already a parent of the collection.",
)
def add_child_collection(id, schema):
    """Add a child collection to the collection specified by the given ID."""
    collection = Collection.query.get_active_or_404(id)
    child_collection = Collection.query.get_active_or_404(schema.load_or_400()["id"])

    try:
        if link_collections(collection, child_collection):
            db.session.commit()
            return json_response(201)

        return json_error_response(409, description="Unable to link collections.")

    except KadiPermissionError as e:
        return json_error_response(403, description=str(e))


@bp.post("/collections/<int:id>/roles/users")
@permission_required("permissions", "collection", "id")
@scopes_required("collection.permissions")
@reqschema(
    UserResourceRoleSchema(only=["user.id", "role.name"]),
    description="The user and corresponding role to add.",
)
@status(201, "User role successfully added to collection.")
@status(409, "A role for that user already exists.")
def add_collection_user_role(id, schema):
    """Add a user role to the collection specified by the given ID."""
    collection = Collection.query.get_active_or_404(id)
    data = schema.load_or_400()
    user = User.query.get_active_or_404(data["user"]["id"])

    if user.is_merged:
        return json_error_response(404)

    return add_role(user, collection, data["role"]["name"])


@bp.post("/collections/<int:id>/roles/groups")
@permission_required("permissions", "collection", "id")
@scopes_required("collection.permissions")
@reqschema(
    GroupResourceRoleSchema(only=["group.id", "role.name"]),
    description="The group and corresponding role to add.",
)
@status(201, "Group role successfully added to collection.")
@status(409, "A role for that group already exists.")
def add_collection_group_role(id, schema):
    """Add a group role to the collection specified by the given ID."""
    collection = Collection.query.get_active_or_404(id)
    data = schema.load_or_400()
    group = Group.query.get_active_or_404(data["group"]["id"])

    return add_role(group, collection, data["role"]["name"])


@bp.post("/collections/<int:id>/restore")
@login_required
@scopes_required("misc.manage_trash")
@status(200, "Return the restored collection.")
def restore_collection(id):
    """Restore the deleted collection specified by the given ID.

    Only the creator of a collection can restore it.
    """
    collection = Collection.query.get_or_404(id)

    if (
        collection.state != CollectionState.DELETED
        or collection.creator != current_user
    ):
        return json_error_response(404)

    _restore_collection(collection)

    return json_response(200, CollectionSchema().dump(collection))


@bp.post("/collections/<int:id>/purge")
@login_required
@scopes_required("misc.manage_trash")
@status(204, "Collection purged successfully.")
def purge_collection(id):
    """Purge the deleted collection specified by the given ID.

    Will remove the collection permanently. Only the creator of a collection can purge
    it.
    """
    collection = Collection.query.get_or_404(id)

    if (
        collection.state != CollectionState.DELETED
        or collection.creator != current_user
    ):
        return json_error_response(404)

    _purge_collection(collection)
    db.session.commit()

    return json_response(204)
