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

import kadi.lib.constants as const
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import internal
from kadi.lib.api.core import json_response
from kadi.lib.conversion import normalize
from kadi.lib.conversion import parse_json_object
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import get_internal_resource_export
from kadi.lib.resources.api import get_selected_resources
from kadi.lib.web import qparam
from kadi.modules.collections.export import get_export_data
from kadi.modules.collections.models import Collection
from kadi.modules.collections.models import CollectionState
from kadi.modules.collections.utils import (
    get_collection_links_graph as _get_collection_links_graph,
)
from kadi.modules.collections.utils import get_parent_collections
from kadi.modules.records.models import Record


@bp.get("/collections/<int:id>/export/internal/<export_type>")
@permission_required("read", "collection", "id")
@internal
@qparam("filter", parse=parse_json_object, default=lambda: {})
@qparam("preview", type=const.QPARAM_TYPE_BOOL, default=False)
@qparam("download", type=const.QPARAM_TYPE_BOOL, default=False)
def get_collection_export_internal(id, export_type, qparams):
    """Export a collection in a specific format."""
    collection = Collection.query.get_active_or_404(id)

    qparams["export_filter"] = qparams.pop("filter")
    return get_internal_resource_export(
        collection, export_type, get_export_data, **qparams
    )


@bp.get("/collections/<int:id>/graph")
@permission_required("read", "collection", "id")
@internal
@qparam("links", default="records")
def get_collection_links_graph(id, qparams):
    """Get links of a collection for visualizing them in a graph."""
    collection = Collection.query.get_active_or_404(id)

    data = _get_collection_links_graph(
        collection,
        records=qparams["links"] == "records",
        children=qparams["links"] == "children",
    )
    return json_response(200, data)


@bp.get("/collections/select")
@login_required
@internal
@qparam("page", type=const.QPARAM_TYPE_INT, default=1)
@qparam("term", parse=normalize)
@qparam("exclude", type=const.QPARAM_TYPE_INT, multiple=True)
@qparam("action", multiple=True)
@qparam("record", type=const.QPARAM_TYPE_INT, default=None)
@qparam("collection", type=const.QPARAM_TYPE_INT, default=None)
def select_collections(qparams):
    """Search collections in dynamic selections.

    Uses :func:`kadi.lib.resources.api.get_selected_resources`.
    """
    excluded_ids = qparams["exclude"]
    record_id = qparams["record"]
    collection_id = qparams["collection"]

    # If applicable, exclude collections that are already linked to the record with the
    # given ID.
    if record_id is not None:
        record = Record.query.get_active(record_id)

        if record is not None and has_permission(
            current_user, "read", "record", record.id
        ):
            collection_ids_query = record.collections.filter(
                Collection.state == CollectionState.ACTIVE
            ).with_entities(Collection.id)
            excluded_ids += [c.id for c in collection_ids_query]

    filters = []

    # If applicable, exclude collections that are already a parent of the collection
    # with the given ID as well as all collections that already have a parent.
    if collection_id is not None:
        filters.append(Collection.parent_id.is_(None))
        collection = Collection.query.get_active(collection_id)

        if collection is not None and has_permission(
            current_user, "read", "collection", collection.id
        ):
            excluded_ids += [c.id for c in get_parent_collections(collection)]

    return get_selected_resources(
        Collection,
        page=qparams["page"],
        filter_term=qparams["term"],
        exclude=excluded_ids,
        actions=qparams["action"],
        filters=filters,
    )
