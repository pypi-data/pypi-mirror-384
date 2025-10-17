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
from kadi.lib.api.utils import status
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import remove_link
from kadi.lib.resources.api import remove_role
from kadi.modules.accounts.models import User
from kadi.modules.collections.core import delete_collection as _delete_collection
from kadi.modules.collections.models import Collection
from kadi.modules.groups.models import Group
from kadi.modules.records.models import Record


@bp.delete("/collections/<int:id>")
@permission_required("delete", "collection", "id")
@scopes_required("collection.delete")
@status(204, "Collection successfully marked as deleted.")
def delete_collection(id):
    """Mark the collection specified by the given ID as deleted.

    Until being removed automatically, a deleted collection may be restored or purged
    using the endpoints `POST /api/collections/{id}/restore` or
    `POST /api/collections/{id}/purge`, respectively.
    """
    collection = Collection.query.get_active_or_404(id)
    _delete_collection(collection)

    return json_response(204)


@bp.delete("/collections/<int:collection_id>/records/<int:record_id>")
@permission_required("link", "collection", "collection_id")
@scopes_required("collection.link")
@status(204, "Record successfully removed from collection.")
def remove_collection_record(collection_id, record_id):
    """Remove a record from a collection.

    Will remove the record specified by the given record ID from the collection
    specified by the given collection ID.
    """
    collection = Collection.query.get_active_or_404(collection_id)
    record = Record.query.get_active_or_404(record_id)

    return remove_link(collection.records, record)


@bp.delete("/collections/<int:collection_id>/collections/<int:child_id>")
@permission_required("link", "collection", "collection_id")
@scopes_required("collection.link")
@status(204, "Child successfully removed from collection.")
def remove_child_collection(collection_id, child_id):
    """Remove a child collection from a collection.

    Will remove the child collection specified by the given child ID from the collection
    specified by the given collection ID.
    """
    collection = Collection.query.get_active_or_404(collection_id)
    child = Collection.query.get_active_or_404(child_id)

    return remove_link(collection.children, child)


@bp.delete("/collections/<int:collection_id>/roles/users/<int:user_id>")
@permission_required("permissions", "collection", "collection_id")
@scopes_required("collection.permissions")
@status(204, "User role successfully removed from collection.")
@status(409, "When trying to remove the creator's role.")
def remove_collection_user_role(collection_id, user_id):
    """Remove a user role from a collection.

    Will remove the role of the user specified by the given user ID from the collection
    specified by the given collection ID.
    """
    collection = Collection.query.get_active_or_404(collection_id)
    user = User.query.get_active_or_404(user_id)

    if user.is_merged:
        return json_error_response(404)

    return remove_role(user, collection)


@bp.delete("/collections/<int:collection_id>/roles/groups/<int:group_id>")
@permission_required("permissions", "collection", "collection_id")
@scopes_required("collection.permissions")
@status(204, "Group role successfully removed from collection.")
def remove_collection_group_role(collection_id, group_id):
    """Remove a group role from a collection.

    Will remove the role of the group specified by the given group ID from the
    collection specified by the given collection ID.
    """
    collection = Collection.query.get_active_or_404(collection_id)
    group = Group.query.get_active_or_404(group_id)

    return remove_role(group, collection)
