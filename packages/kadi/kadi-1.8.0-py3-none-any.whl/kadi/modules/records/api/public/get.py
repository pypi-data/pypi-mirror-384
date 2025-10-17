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
from flask import json
from flask_login import current_user
from flask_login import login_required

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import check_access_token_scopes
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.api.core import scopes_required
from kadi.lib.api.utils import create_pagination_data
from kadi.lib.api.utils import status
from kadi.lib.conversion import lower
from kadi.lib.conversion import normalize
from kadi.lib.conversion import parse_json_object
from kadi.lib.conversion import strip
from kadi.lib.db import escape_like
from kadi.lib.federation import federated_request
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import filter_qparam
from kadi.lib.resources.api import get_resource_group_roles
from kadi.lib.resources.api import get_resource_user_roles
from kadi.lib.resources.api import sort_qparam
from kadi.lib.resources.utils import get_linked_resources
from kadi.lib.resources.utils import get_order_column
from kadi.lib.revisions.models import Revision
from kadi.lib.revisions.schemas import ObjectRevisionSchema
from kadi.lib.tasks.models import Task
from kadi.lib.tasks.models import TaskState
from kadi.lib.utils import as_list
from kadi.lib.utils import compact_json
from kadi.lib.web import download_bytes
from kadi.lib.web import paginated
from kadi.lib.web import qparam
from kadi.lib.web import url_for
from kadi.modules.collections.models import Collection
from kadi.modules.collections.schemas import CollectionSchema
from kadi.modules.records.export import get_extras_export_data
from kadi.modules.records.export import get_record_export_data
from kadi.modules.records.files import stream_files
from kadi.modules.records.models import File
from kadi.modules.records.models import FileState
from kadi.modules.records.models import Record
from kadi.modules.records.models import RecordLink
from kadi.modules.records.models import RecordState
from kadi.modules.records.models import Upload
from kadi.modules.records.models import UploadState
from kadi.modules.records.models import UploadType
from kadi.modules.records.schemas import FileSchema
from kadi.modules.records.schemas import RecordLinkSchema
from kadi.modules.records.schemas import RecordRevisionSchema
from kadi.modules.records.schemas import RecordSchema
from kadi.modules.records.schemas import UploadSchema
from kadi.modules.records.utils import search_records


def _parse_extra_search_queries(extras_str):
    try:
        extras = json.loads(extras_str)
        extras = as_list(extras)
    except:
        return []

    for extra in extras:
        if not isinstance(extra, dict):
            return []

    return extras


@bp.get("/records")
@login_required
@scopes_required("record.read")
@paginated(page_max=100)
@qparam(
    "query",
    parse=strip,
    description="A query to search the records with. Supports exact matches when"
    " surrounded by double quotes.",
)
@qparam(
    "extras",
    parse=_parse_extra_search_queries,
    default=lambda: [],
    description="An URL-encoded array of JSON objects to specify the search within the"
    " extra metadata of a record. See the `extras` parameter in"
    " kadi.modules.records.utils.search_records for a more detailed description (in"
    " Python syntax).",
)
@qparam(
    "sort",
    parse=strip,
    default="_score",
    choice=[
        "_score",
        "last_modified",
        "-last_modified",
        "created_at",
        "-created_at",
        "title",
        "-title",
        "identifier",
        "-identifier",
    ],
    description="The order of the search results. Falls back to `-last_modified` if no"
    " search query is given.",
)
@qparam(
    "visibility",
    parse=strip,
    choice=[const.RESOURCE_VISIBILITY_PRIVATE, const.RESOURCE_VISIBILITY_PUBLIC],
    description="A visibility value to filter the records with.",
)
@qparam(
    "explicit_permissions",
    type=const.QPARAM_TYPE_BOOL,
    default=False,
    description="Flag indicating whether only records with explicit access permissions"
    " should be included, independent of their visibility.",
)
@qparam(
    "user",
    type=const.QPARAM_TYPE_INT,
    multiple=True,
    description="User IDs to filter the records with in relation to their creator."
    " All given users are filtered using an *OR* operation.",
)
@qparam(
    "collection",
    type=const.QPARAM_TYPE_INT,
    multiple=True,
    description="Collection IDs the searched records need to belong to. All given"
    " collections are filtered using an *OR* operation.",
)
@qparam(
    "child_collections",
    type=const.QPARAM_TYPE_BOOL,
    default=False,
    description="Flag indicating whether the children of the filtered collections"
    " should be included.",
)
@qparam(
    "type",
    multiple=True,
    parse=[lower, normalize],
    description="Record types to filter the records with. All given types are filtered"
    " using an *OR* operation.",
)
@qparam(
    "tag",
    multiple=True,
    parse=[lower, normalize],
    description="Tags to filter the records with. All given tags are filtered using the"
    " operator specified via the **tag_operator**.",
)
@qparam(
    "tag_operator",
    parse=[lower, strip],
    default="or",
    choice=["or", "and"],
    description="The operator to filter the tags with.",
)
@qparam(
    "mimetype",
    multiple=True,
    parse=[lower, strip],
    description="MIME types to filter the records with based on their files. All given"
    " MIME types are filtered using an *OR* operation.",
)
@qparam(
    "instance",
    description="The name of an external Kadi4Mat instance to search instead.",
)
@status(200, "Return a paginated array of records.")
@status(
    400,
    "The specified external Kadi4Mat instance is invalid or has not yet been connected"
    " to the current user's account.",
)
@status(502, "The request to the specified external Kadi4Mat instance failed.")
def get_records(page, per_page, qparams):
    """Search and filter for records."""
    if qparams["instance"]:
        params = {"page": page, "per_page": per_page, **qparams}

        for param in ["instance", "user", "collection"]:
            params.pop(param, None)

        return federated_request(qparams["instance"], "records", params=params)

    records, total_records = search_records(
        search_query=qparams["query"],
        page=page,
        per_page=per_page,
        sort=qparams["sort"],
        visibility=qparams["visibility"],
        explicit_permissions=qparams["explicit_permissions"],
        user_ids=qparams["user"],
        collection_ids=qparams["collection"],
        child_collections=qparams["child_collections"],
        record_types=qparams["type"],
        tags=qparams["tag"],
        tag_operator=qparams["tag_operator"],
        mimetypes=qparams["mimetype"],
        extras=qparams["extras"],
    )

    data = {
        "items": RecordSchema(many=True).dump(records),
        "_actions": {"new_record": url_for("api.new_record")},
        **create_pagination_data(
            total_records,
            page,
            per_page,
            **{**qparams, "extras": compact_json(qparams["extras"])},
        ),
    }

    return json_response(200, data)


@bp.get("/records/<int:id>")
@permission_required("read", "record", "id")
@scopes_required("record.read")
@status(200, "Return the record.")
def get_record(id):
    """Get the record specified by the given ID."""
    record = Record.query.get_active_or_404(id)
    return json_response(200, RecordSchema().dump(record))


@bp.get("/records/identifier/<identifier:identifier>")
@login_required
@scopes_required("record.read")
@status(200, "Return the record.")
def get_record_by_identifier(identifier):
    """Get the record specified by the given identifier."""
    record = Record.query.filter_by(
        identifier=identifier, state=RecordState.ACTIVE
    ).first_or_404()

    if not has_permission(current_user, "read", "record", record.id):
        return json_error_response(403)

    return json_response(200, RecordSchema().dump(record))


@bp.get("/records/<int:id>/records")
@permission_required("read", "record", "id")
@scopes_required("record.read")
@paginated
@qparam(
    "direction",
    parse=strip,
    default="out",
    description="The direction of the record links. `out` will return outgoing links"
    " from the current record, while `in` will return incoming links to the current"
    " record. Depending on direction, linked records will be included as `record_to` or"
    " `record_from` respectively.",
)
@qparam(
    "filter",
    parse=normalize,
    description="A query to filter the record links by their link name or the linked"
    " records by their title or identifier.",
)
@qparam(
    "sort",
    parse=strip,
    default="-last_modified",
    choice=[
        "last_modified",
        "-last_modified",
        "created_at",
        "-created_at",
        "name",
        "-name",
    ],
    description="The order of the returned record links.",
)
@qparam(
    "action",
    multiple=True,
    parse=strip,
    description="Further actions the current user needs permission to perform in the"
    " linked records.",
)
@status(200, "Return a paginated array of record links.")
def get_record_links(id, page, per_page, qparams):
    """Get the record links of the record specified by the given ID."""
    record = Record.query.get_active_or_404(id)

    sort = qparams["sort"]
    order_columm = RecordLink.last_modified.desc()

    if sort == "last_modified":
        order_columm = RecordLink.last_modified
    elif sort == "-last_modified":
        order_columm = RecordLink.last_modified.desc()
    elif sort == "created_at":
        order_columm = RecordLink.created_at
    elif sort == "-created_at":
        order_columm = RecordLink.created_at.desc()
    elif sort == "name":
        order_columm = RecordLink.name
    elif sort == "-name":
        order_columm = RecordLink.name.desc()

    record_ids_query = (
        get_permitted_objects(current_user, "read", "record")
        .filter(Record.state == RecordState.ACTIVE)
        .with_entities(Record.id)
    )

    for action in set(qparams["action"]):
        record_ids_query = (
            get_permitted_objects(current_user, action, "record")
            .with_entities(Record.id)
            .intersect(record_ids_query)
        )

    if qparams["direction"] == "in":
        excluded_attr = "record_to"
        record_links = record.linked_from.join(RecordLink.record_from).filter(
            RecordLink.record_from_id.in_(record_ids_query)
        )
    else:
        excluded_attr = "record_from"
        record_links = record.links_to.join(RecordLink.record_to).filter(
            RecordLink.record_to_id.in_(record_ids_query)
        )

    schema = RecordLinkSchema(current_record=record, many=True, exclude=[excluded_attr])

    filter_term = escape_like(qparams["filter"])
    paginated_record_links = (
        record_links.filter(
            db.or_(
                RecordLink.name.ilike(f"%{filter_term}%"),
                Record.title.ilike(f"%{filter_term}%"),
                Record.identifier.ilike(f"%{filter_term}%"),
            ),
        )
        .order_by(order_columm)
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    data = {
        "items": schema.dump(paginated_record_links),
        **create_pagination_data(
            paginated_record_links.total, page, per_page, id=record.id, **qparams
        ),
    }

    return json_response(200, data)


@bp.get("/records/<int:record_id>/records/<int:link_id>")
@permission_required("read", "record", "record_id")
@scopes_required("record.read")
@status(200, "Return the record link.")
def get_record_link(record_id, link_id):
    """Get a record link.

    Will return the outgoing record link specified by the given link ID from the record
    specified by the given record ID.
    """
    record_from = Record.query.get_active_or_404(record_id)
    record_link = record_from.links_to.filter(RecordLink.id == link_id).first_or_404()
    record_to = record_link.record_to

    if record_to.state != RecordState.ACTIVE:
        return json_error_response(404)

    if not has_permission(current_user, "read", "record", record_to.id):
        return json_error_response(403)

    return json_response(
        200, RecordLinkSchema(exclude=["record_from"]).dump(record_link)
    )


@bp.get("/records/records/<int:id>")
@login_required
@scopes_required("record.read")
@status(200, "Return the record link.")
def get_record_link_by_id(id):
    """Get a record link directly by its ID."""
    record_link = RecordLink.query.get_or_404(id)
    record_to = record_link.record_to
    record_from = record_link.record_from

    if record_to.state != RecordState.ACTIVE or record_from.state != RecordState.ACTIVE:
        return json_error_response(404)

    if not has_permission(
        current_user, "read", "record", record_to.id
    ) or not has_permission(current_user, "read", "record", record_from.id):
        return json_error_response(403)

    return json_response(200, RecordLinkSchema().dump(record_link))


@bp.get("/records/<int:id>/collections")
@permission_required("read", "record", "id")
@scopes_required("record.read", "collection.read")
@paginated
@filter_qparam("collections")
@sort_qparam("collections")
@qparam(
    "action",
    multiple=True,
    parse=strip,
    description="Further actions the current user needs permission to perform in the"
    " linked collections.",
)
@status(200, "Return a paginated array of collections.")
def get_record_collections(id, page, per_page, qparams):
    """Get collections the record specified by the given ID is part of."""
    record = Record.query.get_active_or_404(id)

    filter_term = escape_like(qparams["filter"])
    order_columm = get_order_column(Collection, qparams["sort"])

    paginated_collections = (
        get_linked_resources(Collection, record.collections, actions=qparams["action"])
        .filter(
            db.or_(
                Collection.title.ilike(f"%{filter_term}%"),
                Collection.identifier.ilike(f"%{filter_term}%"),
            ),
        )
        .order_by(order_columm)
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    data = {
        "items": CollectionSchema(many=True, linked_record=record).dump(
            paginated_collections
        ),
        **create_pagination_data(
            paginated_collections.total, page, per_page, id=record.id, **qparams
        ),
    }

    return json_response(200, data)


@bp.get("/records/<int:id>/roles/users")
@permission_required("read", "record", "id")
@scopes_required("record.read", "user.read")
@paginated
@qparam(
    "filter",
    parse=strip,
    description="A query to filter the users by their username or display name.",
)
@qparam(
    "exclude",
    type=const.QPARAM_TYPE_INT,
    multiple=True,
    description="User IDs to exclude.",
)
@status(
    200,
    "Return a paginated array of user roles, sorted by role name and then by user ID in"
    " ascending order. The creator will always be listed first.",
)
def get_record_user_roles(id, page, per_page, qparams):
    """Get user roles of the record specified by the given ID."""
    record = Record.query.get_active_or_404(id)

    items, total = get_resource_user_roles(
        record,
        page=page,
        per_page=per_page,
        filter_term=qparams["filter"],
        exclude=qparams["exclude"],
    )
    data = {
        "items": items,
        **create_pagination_data(total, page, per_page, id=record.id),
    }

    return json_response(200, data)


@bp.get("/records/<int:id>/roles/groups")
@permission_required("read", "record", "id")
@scopes_required("record.read", "group.read")
@paginated
@qparam(
    "filter",
    parse=normalize,
    description="A query to filter the groups by their title or identifier.",
)
@status(
    200,
    "Return a paginated array of group roles, sorted by role name and then by group ID"
    " in ascending order.",
)
def get_record_group_roles(id, page, per_page, qparams):
    """Get group roles of the record specified by the given ID.

    If a user can manage permissions of this record, all group roles are returned.
    However, groups that a user can normally not read include only a limited subset of
    attributes (`id`, `title`, `identifier` and `visibility`).
    """
    record = Record.query.get_active_or_404(id)

    items, total = get_resource_group_roles(
        record, page=page, per_page=per_page, filter_term=qparams["filter"]
    )
    data = {
        "items": items,
        **create_pagination_data(total, page, per_page, id=record.id),
    }

    return json_response(200, data)


@bp.get("/records/<int:id>/revisions")
@permission_required("read", "record", "id")
@scopes_required("record.read")
@paginated
@status(
    200,
    "Return a paginated array of record revisions, sorted by revision timestamp in"
    " descending order.",
)
def get_record_revisions(id, page, per_page):
    """Get record revisions of the record specified by the given ID."""
    record = Record.query.get_active_or_404(id)
    paginated_revisions = record.ordered_revisions.paginate(
        page=page, per_page=per_page, error_out=False
    )

    schema = ObjectRevisionSchema(
        RecordRevisionSchema,
        many=True,
        api_endpoint="api.get_record_revision",
        view_endpoint="records.view_record_revision",
        endpoint_args={"record_id": record.id},
    )
    data = {
        "items": schema.dump(paginated_revisions),
        **create_pagination_data(
            paginated_revisions.total, page, per_page, id=record.id
        ),
    }

    return json_response(200, data)


@bp.get("/records/<int:record_id>/revisions/<int:revision_id>")
@permission_required("read", "record", "record_id")
@scopes_required("record.read")
@qparam(
    "revision",
    type=const.QPARAM_TYPE_INT,
    default=None,
    description="The ID of a revision to compare with instead of the previous one.",
)
@status(200, "Return the record revision.")
def get_record_revision(record_id, revision_id, qparams):
    """Get a record revision.

    Will return the record revision specified by the given revision ID of the record
    specified by the given record ID.
    """
    record = Record.query.get_active_or_404(record_id)
    revision = record.revisions.filter(
        Record.revision_class.id == revision_id
    ).first_or_404()

    compared_revision = None

    if compared_revision_id := qparams["revision"]:
        compared_revision = record.revisions.filter(
            Record.revision_class.id == compared_revision_id
        ).first()

    schema = ObjectRevisionSchema(
        RecordRevisionSchema,
        compared_revision=compared_revision,
        api_endpoint="api.get_record_revision",
        view_endpoint="records.view_record_revision",
        endpoint_args={"record_id": record.id},
    )

    return json_response(200, schema.dump(revision))


@bp.get("/records/<int:id>/export/<export_type>")
@permission_required("read", "record", "id")
@scopes_required("record.read")
@qparam(
    "filter",
    parse=parse_json_object,
    default=lambda: {},
    description="An URL-encoded JSON object to specify various filters to adjust"
    " the returned export data. See the `export_filter` parameter in"
    " kadi.modules.records.export.get_record_export_data for a more detailed"
    " description (in Python syntax).",
)
@status(200, "Return the exported record data.")
def get_record_export(id, export_type, qparams):
    """Export the record specified by the given ID using the given export type.

    Currently, `json`, `rdf`, `pdf`, `qr` and `ro-crate` are supported as export types.
    """
    record = Record.query.get_active_or_404(id)
    export_types = const.EXPORT_TYPES["record"]

    if export_type not in export_types:
        return json_error_response(404)

    export_filter = qparams["filter"]

    # Always exclude the user information if the access token scopes are insufficient.
    if not check_access_token_scopes("user.read"):
        export_filter["user"] = True

    export_data = get_record_export_data(
        record, export_type, export_filter=export_filter
    )

    file_ext = export_types[export_type]["ext"]
    filename = f"{record.identifier}.{file_ext}"

    kwargs = {"filename": filename}

    if export_type == const.EXPORT_TYPE_RO_CRATE:
        if export_filter.get("metadata_only", False):
            kwargs["filename"] = f"{record.identifier}.jsonld"
        else:
            kwargs.update(mimetype=const.MIMETYPE_ZIP, content_length=len(export_data))

    return download_bytes(export_data, **kwargs)


@bp.get("/records/<int:id>/extras/export/<export_type>")
@permission_required("read", "record", "id")
@scopes_required("record.read")
@qparam(
    "filter",
    parse=parse_json_object,
    default=lambda: {},
    description="An URL-encoded JSON object to specify various filters to adjust"
    " the returned export data. See the `export_filter` parameter in"
    " kadi.modules.records.export.get_extras_export_data for a more detailed"
    " description (in Python syntax).",
)
@status(200, "Return the exported extras data.")
def get_extras_export(id, export_type, qparams):
    """Export the extras of a record specified by the given ID.

    Currently, only `json` is supported as export type.
    """
    record = Record.query.get_active_or_404(id)
    export_types = const.EXPORT_TYPES["extras"]

    if export_type not in export_types:
        return json_error_response(404)

    data = get_extras_export_data(record, export_type, export_filter=qparams["filter"])

    file_ext = export_types[export_type]["ext"]
    filename = f"{record.identifier}-extras.{file_ext}"

    return download_bytes(data, filename=filename)


@bp.get("/records/<int:id>/files")
@permission_required("read", "record", "id")
@scopes_required("record.read")
@paginated
@qparam("filter", parse=normalize, description="A query to filter the files by name.")
@qparam(
    "sort",
    parse=strip,
    default="-last_modified",
    choice=[
        "last_modified",
        "-last_modified",
        "created_at",
        "-created_at",
        "name",
        "-name",
        "size",
        "-size",
    ],
    description="The order of the returned files.",
)
@status(200, "Return a paginated array of files.")
def get_files(id, page, per_page, qparams):
    """Get files of the record specified by the given ID."""
    record = Record.query.get_active_or_404(id)

    sort = qparams["sort"]
    order_columm = File.last_modified.desc()

    if sort == "last_modified":
        order_columm = File.last_modified
    elif sort == "-last_modified":
        order_columm = File.last_modified.desc()
    elif sort == "created_at":
        order_columm = File.created_at
    elif sort == "-created_at":
        order_columm = File.created_at.desc()
    elif sort == "name":
        order_columm = File.name
    elif sort == "-name":
        order_columm = File.name.desc()
    elif sort == "size":
        order_columm = File.size
    elif sort == "-size":
        order_columm = File.size.desc()

    paginated_files = (
        record.active_files.filter(
            File.name.ilike(f"%{escape_like(qparams['filter'])}%")
        )
        .order_by(order_columm)
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    data = {
        "items": FileSchema(many=True).dump(paginated_files),
        **create_pagination_data(
            paginated_files.total, page, per_page, id=record.id, **qparams
        ),
    }

    return json_response(200, data)


@bp.get("/records/<int:record_id>/files/<uuid:file_id>")
@permission_required("read", "record", "record_id")
@scopes_required("record.read")
@status(200, "Return the file.")
def get_file(record_id, file_id):
    """Get a file of a record.

    Will return the file specified by the given file ID of the record specified by the
    given record ID.
    """
    record = Record.query.get_active_or_404(record_id)
    file = record.active_files.filter(File.id == file_id).first_or_404()

    return json_response(200, FileSchema().dump(file))


@bp.get("/records/<int:record_id>/files/name/<path:filename>")
@permission_required("read", "record", "record_id")
@scopes_required("record.read")
@status(200, "Return the file.")
def get_file_by_name(record_id, filename):
    """Get a file of a record by its name.

    Will return the file specified by the given filename of the record specified by the
    given record ID.
    """
    record = Record.query.get_active_or_404(record_id)
    file = record.active_files.filter(File.name == filename).first_or_404()

    return json_response(200, FileSchema().dump(file))


@bp.get("/records/files/<uuid:id>")
@login_required
@scopes_required("record.read")
@status(200, "Return the file.")
def get_file_by_id(id):
    """Get a file of a record directly by its ID."""
    file = File.query.get_active_or_404(id)
    record = file.record

    if record.state != RecordState.ACTIVE:
        return json_error_response(404)

    if not has_permission(current_user, "read", "record", record.id):
        return json_error_response(403)

    return json_response(200, FileSchema().dump(file))


@bp.get("/records/<int:record_id>/files/<uuid:file_id>/download")
@permission_required("read", "record", "record_id")
@scopes_required("record.read")
@status(200, "Return the file as attachment.")
def download_file(record_id, file_id):
    """Download a file of a record.

    Will return the file specified by the given file ID of the record specified by the
    given record ID as attachment.
    """
    record = Record.query.get_active_or_404(record_id)
    file = record.active_files.filter(File.id == file_id).first_or_404()

    return file.storage.download(
        file.identifier, filename=file.name, mimetype=file.mimetype
    )


@bp.get("/records/<int:id>/files/download")
@permission_required("read", "record", "id")
@scopes_required("record.read")
@status(200, "Return the files as attachment.")
def download_files(id):
    """Download all files of a record.

    Will return all files of the record specified by the given ID as a ZIP archive as
    attachment.
    """
    record = Record.query.get_active_or_404(id)
    return stream_files(record)


@bp.get("/records/<int:id>/files/revisions")
@permission_required("read", "record", "id")
@scopes_required("record.read")
@paginated
@status(
    200,
    "Return a paginated array of file revisions, sorted by revision timestamp in"
    " descending order.",
)
def get_file_revisions(id, page, per_page):
    """Get file revisions of the record specified by the given ID."""
    record = Record.query.get_active_or_404(id)

    paginated_revisions = (
        File.revision_class.query.join(File)
        .join(Revision)
        .filter(File.record_id == record.id)
        .order_by(Revision.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    schema = ObjectRevisionSchema(
        FileSchema,
        many=True,
        api_endpoint="api.get_file_revision",
        view_endpoint="records.view_file_revision",
        endpoint_args={"record_id": record.id},
    )
    data = {
        "items": schema.dump(paginated_revisions),
        **create_pagination_data(
            paginated_revisions.total, page, per_page, id=record.id
        ),
    }

    return json_response(200, data)


@bp.get("/records/<int:record_id>/files/revisions/<int:revision_id>")
@permission_required("read", "record", "record_id")
@scopes_required("record.read")
@qparam(
    "revision",
    type=const.QPARAM_TYPE_INT,
    default=None,
    description="The ID of a revision to compare with instead of the previous one.",
)
@status(200, "Return the file revision.")
def get_file_revision(record_id, revision_id, qparams):
    """Get a file revision.

    Will return the file revision specified by the given revision ID of the record
    specified by the given record ID.
    """
    record = Record.query.get_active_or_404(record_id)
    revision = File.revision_class.query.get_or_404(revision_id)

    if record.id != revision.file.record_id:
        return json_error_response(404)

    view_file_url = None

    if revision.file.state == FileState.ACTIVE:
        view_file_url = url_for(
            "records.view_file", record_id=record.id, file_id=revision.file.id
        )

    compared_revision = None

    if compared_revision_id := qparams["revision"]:
        compared_revision = revision.file.revisions.filter(
            File.revision_class.id == compared_revision_id
        ).first()

    schema = ObjectRevisionSchema(
        FileSchema,
        compared_revision=compared_revision,
        api_endpoint="api.get_file_revision",
        view_endpoint="records.view_file_revision",
        endpoint_args={"record_id": record.id},
        view_object_url=view_file_url,
    )

    return json_response(200, schema.dump(revision))


@bp.get("/records/<int:id>/uploads")
@permission_required("update", "record", "id")
@scopes_required("record.update")
@status(200, "Return the uploads, sorted by creation date in ascending order.")
def get_uploads(id):
    """Get all active and processing uploads of the record specified by the given ID.

    Only uploads owned by the current user will be returned. The required size for
    uploading chunks (except for the final chunk for chunked uploads) is returned as the
    `_meta.chunk_size` property of each upload. For direct uploads, the chunk size is
    always equal to the total upload size.
    """
    record = Record.query.get_active_or_404(id)
    uploads = record.uploads.filter(
        Upload.user_id == current_user.id,
        Upload.state.in_([UploadState.ACTIVE, UploadState.PROCESSING]),
    ).order_by(Upload.created_at)

    return json_response(200, {"items": UploadSchema(many=True).dump(uploads)})


@bp.get("/records/<int:record_id>/uploads/<uuid:upload_id>")
@permission_required("update", "record", "record_id")
@scopes_required("record.update")
@status(200, "Return the upload.")
def get_upload(record_id, upload_id):
    """Get an upload of a record.

    Will return the upload specified by the given upload ID of the record specified by
    the given record ID. Only uploads owned by the current user can be retrieved.

    For chunked uploads, this endpoint can also be used to query the state of the upload
    processing task after the upload has been finished. The task will be included as the
    `_meta.task` property, and includes its `state` and, for uploads that have finished
    processing, either the newly created `file` when the processing task finished
    successfully or an `error` message otherwise.
    """
    record = Record.query.get_active_or_404(record_id)
    upload = record.uploads.filter(
        Upload.id == upload_id, Upload.user_id == current_user.id
    ).first_or_404()

    data = UploadSchema().dump(upload)

    if upload.upload_type == UploadType.CHUNKED and upload.state != UploadState.ACTIVE:
        task = Task.query.filter(
            Task.name == const.TASK_MERGE_CHUNKS,
            Task.arguments["args"][0].astext == str(upload.id),
        ).first_or_404()

        task_data = {"state": task.state}

        if task.state == TaskState.SUCCESS:
            file = File.query.get(task.result["file"])
            task_data["file"] = FileSchema().dump(file)
        elif task.state == TaskState.FAILURE:
            task_data["error"] = task.result["error"]

        data["_meta"]["task"] = task_data

    return json_response(200, data)
