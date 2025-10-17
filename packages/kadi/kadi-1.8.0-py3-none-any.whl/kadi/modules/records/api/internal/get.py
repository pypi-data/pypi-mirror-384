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
from flask import render_template
from flask_login import current_user
from flask_login import login_required

import kadi.lib.constants as const
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import internal
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.conversion import clamp
from kadi.lib.conversion import normalize
from kadi.lib.conversion import parse_json_object
from kadi.lib.conversion import strip
from kadi.lib.db import escape_like
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import get_internal_resource_export
from kadi.lib.resources.api import get_selected_resources
from kadi.lib.web import qparam
from kadi.lib.web import url_for
from kadi.modules.collections.models import Collection
from kadi.modules.records.export import get_record_export_data
from kadi.modules.records.files import get_permitted_files
from kadi.modules.records.links import get_record_links_graph as _get_record_links_graph
from kadi.modules.records.models import File
from kadi.modules.records.models import FileState
from kadi.modules.records.models import Record
from kadi.modules.records.models import RecordLink
from kadi.modules.records.models import RecordState
from kadi.modules.records.previews import get_preview_data


@bp.get("/records/<int:id>/export/internal/<export_type>")
@permission_required("read", "record", "id")
@internal
@qparam("filter", parse=parse_json_object, default=lambda: {})
@qparam("preview", type=const.QPARAM_TYPE_BOOL, default=False)
@qparam("download", type=const.QPARAM_TYPE_BOOL, default=False)
def get_record_export_internal(id, export_type, qparams):
    """Export a record in a specific format."""
    record = Record.query.get_active_or_404(id)

    qparams["export_filter"] = qparams.pop("filter")
    return get_internal_resource_export(
        record, export_type, get_record_export_data, **qparams
    )


@bp.get("/records/<int:id>/graph")
@permission_required("read", "record", "id")
@internal
@qparam(
    "depth",
    type=const.QPARAM_TYPE_INT,
    parse=[int, lambda x: clamp(x, 1, 3)],
    default=1,
)
@qparam("direction")
def get_record_links_graph(id, qparams):
    """Get links of a record for visualizing them in a graph."""
    record = Record.query.get_active_or_404(id)

    data = _get_record_links_graph(record, qparams["depth"], qparams["direction"])
    return json_response(200, data)


@bp.get("/records/<int:record_id>/files/<uuid:file_id>/preview")
@permission_required("read", "record", "record_id")
@internal
def get_file_preview(record_id, file_id):
    """Get the preview data of a file.

    The actual preview data may either consist of a URL or the preview data itself,
    depending on the preview type. In the first case, a browser may be able to directly
    preview the file using the returned URL.
    """
    record = Record.query.get_active_or_404(record_id)
    file = record.active_files.filter(File.id == file_id).first_or_404()

    preview_data = get_preview_data(file)

    if preview_data is None:
        return json_error_response(404)

    return json_response(200, {"type": preview_data[0], "data": preview_data[1]})


@bp.get("/records/<int:record_id>/files/<uuid:file_id>/preview/file")
@permission_required("read", "record", "record_id")
@internal
def preview_file(record_id, file_id):
    """Preview a file directly in the browser."""
    record = Record.query.get_active_or_404(record_id)
    file = record.active_files.filter(File.id == file_id).first_or_404()

    if file.magic_mimetype in {const.MIMETYPE_PDF, *const.IMAGE_MIMETYPES}:
        return file.storage.download(
            file.identifier,
            filename=file.name,
            mimetype=file.magic_mimetype,
            as_attachment=False,
        )

    return json_error_response(404)


@bp.get("/records/select")
@login_required
@internal
@qparam("page", type=const.QPARAM_TYPE_INT, default=1)
@qparam("term", parse=normalize)
@qparam("exclude", type=const.QPARAM_TYPE_INT, multiple=True)
@qparam("action", multiple=True)
@qparam("collection", type=const.QPARAM_TYPE_INT, default=None)
def select_records(qparams):
    """Search records in dynamic selections.

    Uses :func:`kadi.lib.resources.api.get_selected_resources`.
    """
    excluded_ids = qparams["exclude"]
    collection_id = qparams["collection"]

    # If applicable, exclude records that are already linked to the collection with the
    # given ID.
    if collection_id is not None:
        collection = Collection.query.get_active(collection_id)

        if collection is not None and has_permission(
            current_user, "read", "collection", collection.id
        ):
            record_ids_query = collection.records.filter(
                Record.state == RecordState.ACTIVE
            ).with_entities(Record.id)
            excluded_ids += [r.id for r in record_ids_query]

    return get_selected_resources(
        Record,
        page=qparams["page"],
        filter_term=qparams["term"],
        exclude=excluded_ids,
        actions=qparams["action"],
    )


@bp.get("/records/types/select")
@login_required
@internal
@qparam("page", type=const.QPARAM_TYPE_INT, default=1)
@qparam("term", parse=normalize)
def select_record_types(qparams):
    """Search record types in dynamic selections.

    Similar to :func:`kadi.lib.resources.api.get_selected_resources`. Only the types of
    records the current user has read permission for are returned.
    """
    paginated_records = (
        get_permitted_objects(current_user, "read", "record")
        .filter(
            Record.state == RecordState.ACTIVE,
            Record.type.is_not(None),
            Record.type.ilike(f"%{escape_like(qparams['term'])}%"),
        )
        .distinct()
        .order_by(Record.type)
        .with_entities(Record.type)
        .paginate(page=qparams["page"], per_page=10, error_out=False)
    )

    data = {
        "results": [],
        "pagination": {"more": paginated_records.has_next},
    }
    for record in paginated_records:
        data["results"].append({"id": record.type, "text": record.type})

    return json_response(200, data)


@bp.get("/records/mimetypes/select")
@login_required
@internal
@qparam("page", type=const.QPARAM_TYPE_INT, default=1)
@qparam("term", parse=strip)
def select_mimetypes(qparams):
    """Search MIME types of record files in dynamic selections.

    Similar to :func:`kadi.lib.resources.api.get_selected_resources`. Only the MIME
    types of files the current user has read permission for are returned.
    """
    paginated_files = (
        get_permitted_objects(current_user, "read", "record")
        .join(Record.files)
        .filter(
            Record.state == RecordState.ACTIVE,
            File.state == FileState.ACTIVE,
            File.mimetype.ilike(f"%{escape_like(qparams['term'])}%"),
        )
        .distinct()
        .order_by(File.mimetype)
        .with_entities(File.mimetype)
        .paginate(page=qparams["page"], per_page=10, error_out=False)
    )

    data = {
        "results": [],
        "pagination": {"more": paginated_files.has_next},
    }
    for file in paginated_files:
        data["results"].append({"id": file.mimetype, "text": file.mimetype})

    return json_response(200, data)


@bp.get("/records/files/select")
@login_required
@internal
@qparam("page", type=const.QPARAM_TYPE_INT, default=1)
@qparam("term", parse=strip)
@qparam("record", type=const.QPARAM_TYPE_INT, default=None)
@qparam("order_by_record", type=const.QPARAM_TYPE_INT, default=None)
@qparam("mimetype", multiple=True)
def select_files(qparams):
    """Search record files in dynamic selections.

    Similar to :func:`kadi.lib.resources.api.get_selected_resources`. Only the files of
    records the current user has read permission for are returned.
    """
    files_query = get_permitted_files(
        filter_term=qparams["term"], record_id=qparams["record"]
    )

    # Exclude files not matching the MIME types.
    if mimetypes := qparams["mimetype"]:
        files_query = files_query.filter(File.magic_mimetype.in_(mimetypes))

    order = [File.name]

    # List all files belonging to a certain record first.
    if (order_by_record_id := qparams["order_by_record"]) is not None:
        order.insert(0, Record.id != order_by_record_id)

    paginated_files = files_query.order_by(*order).paginate(
        page=qparams["page"], per_page=10, error_out=False
    )

    data = {
        "results": [],
        "pagination": {"more": paginated_files.has_next},
    }
    for file in paginated_files:
        endpoint_args = {"record_id": file.record_id, "file_id": file.id}
        data["results"].append(
            {
                "id": file.id,
                "text": file.name,
                "view_endpoint": url_for("records.view_file", **endpoint_args),
                "preview_endpoint": url_for("api.preview_file", **endpoint_args),
                "download_endpoint": url_for("api.download_file", **endpoint_args),
                "delete_endpoint": url_for("api.delete_file", **endpoint_args),
                "body": render_template(
                    "records/snippets/select_file.html",
                    file=file,
                    record_id=qparams["record"],
                    highlighted_record_id=qparams["order_by_record"],
                ),
            }
        )

    return json_response(200, data)


@bp.get("/records/links/select")
@login_required
@internal
@qparam("page", type=const.QPARAM_TYPE_INT, default=1)
@qparam("term", parse=strip)
def select_link_names(qparams):
    """Search the names of record links in dynamic selections.

    Similar to :func:`kadi.lib.resources.api.get_selected_resources`. Only the links of
    records the current user has read permission for are returned.
    """
    record_ids_query = (
        get_permitted_objects(current_user, "read", "record")
        .filter(Record.state == RecordState.ACTIVE)
        .with_entities(Record.id)
    )

    paginated_record_links = (
        RecordLink.query.filter(
            RecordLink.record_from_id.in_(record_ids_query),
            RecordLink.record_to_id.in_(record_ids_query),
            RecordLink.name.ilike(f"%{escape_like(qparams['term'])}%"),
        )
        .distinct()
        .order_by(RecordLink.name)
        .with_entities(RecordLink.name)
        .paginate(page=qparams["page"], per_page=10, error_out=False)
    )

    data = {
        "results": [],
        "pagination": {"more": paginated_record_links.has_next},
    }
    for record_link in paginated_record_links:
        data["results"].append({"id": record_link.name, "text": record_link.name})

    return json_response(200, data)
