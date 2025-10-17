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
from flask import abort
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask_babel import gettext as _
from flask_login import current_user
from flask_login import login_required

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.exceptions import KadiPermissionError
from kadi.lib.exceptions import KadiValidationError
from kadi.lib.federation import get_federated_instances
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.utils import permission_required
from kadi.lib.plugins.core import run_hook
from kadi.lib.publication import get_publication_provider
from kadi.lib.publication import get_publication_providers
from kadi.lib.resources.tasks import start_publish_resource_task
from kadi.lib.resources.utils import get_linked_resources
from kadi.lib.resources.views import add_links
from kadi.lib.resources.views import update_roles
from kadi.lib.revisions.models import Revision
from kadi.lib.validation import validate_uuid
from kadi.lib.web import flash_danger
from kadi.lib.web import flash_info
from kadi.lib.web import flash_success
from kadi.lib.web import flash_warning
from kadi.lib.web import html_error_response
from kadi.lib.web import qparam
from kadi.lib.web import url_for
from kadi.modules.accounts.models import User
from kadi.modules.collections.models import Collection
from kadi.modules.collections.models import CollectionState
from kadi.modules.records.models import RecordState
from kadi.modules.templates.models import Template
from kadi.modules.templates.models import TemplateType

from .blueprint import bp
from .core import create_record
from .core import delete_record as _delete_record
from .core import update_record
from .files import delete_file as _delete_file
from .files import get_direct_upload_type
from .files import update_file
from .forms import AddRecordLinksForm
from .forms import AddRolesForm
from .forms import EditFileForm
from .forms import EditRecordForm
from .forms import EditRecordLinkForm
from .forms import LinkCollectionsForm
from .forms import NewRecordForm
from .imports import parse_import_data
from .links import create_record_links
from .links import get_linked_record
from .links import get_record_link_changes
from .links import remove_record_link as _remove_record_link
from .links import update_record_link
from .models import File
from .models import Record
from .models import RecordLink
from .schemas import FileSchema
from .schemas import RecordSchema


@bp.get("")
@login_required
@qparam("user", type=const.QPARAM_TYPE_INT, multiple=True)
@qparam("collection", type=const.QPARAM_TYPE_INT, multiple=True)
def records(qparams):
    """Record overview page.

    Allows users to search and filter for records or create new ones.
    """
    users = []
    collections = []

    if user_ids := qparams["user"]:
        users_query = User.query.filter(User.id.in_(user_ids))
        users = [(u.id, f"@{u.identity.username}") for u in users_query]

    if collection_ids := qparams["collection"]:
        collections_query = (
            get_permitted_objects(current_user, "read", "collection")
            .filter(
                Collection.state == CollectionState.ACTIVE,
                Collection.id.in_(collection_ids),
            )
            .with_entities(Collection.id, Collection.identifier)
        )
        collections = [(c.id, f"@{c.identifier}") for c in collections_query]

    return render_template(
        "records/records.html",
        title=_("Records"),
        js_context={
            "instances": get_federated_instances(user=current_user),
            "users": users,
            "collections": collections,
        },
    )


def _get_copied_record(record_id):
    if request.method != "GET" or record_id is None:
        return None

    record = Record.query.get_active(record_id)

    if record is not None and has_permission(current_user, "read", "record", record.id):
        return record

    return None


def _get_current_template(template_id):
    if request.method != "GET" or template_id is None:
        return None

    template = Template.query.get_active(template_id)

    if (
        template is not None
        and template.type in {TemplateType.RECORD, TemplateType.EXTRAS}
        and has_permission(current_user, "read", "template", template.id)
    ):
        return template

    return None


def _get_linked_collection(collection_id):
    # Do not ignore POST requests here to allow combining a linked collection parameter
    # with import data.
    if collection_id is None:
        return None

    collection = Collection.query.get_active(collection_id)

    if collection is not None and has_permission(
        current_user, "link", "collection", collection.id
    ):
        return collection

    return None


@bp.route("/new", methods=["GET", "POST"])
@permission_required("create", "record", None)
@qparam("record", type=const.QPARAM_TYPE_INT, default=None)
@qparam("template", type=const.QPARAM_TYPE_INT, default=None)
@qparam("collection", type=const.QPARAM_TYPE_INT, default=None)
@qparam("redirect", default="files")
def new_record(qparams):
    """Page to create a new record."""
    import_data = None
    import_type = request.form.get("import_type")

    if import_type and "import_data" in request.files:
        import_data = parse_import_data(request.files["import_data"], import_type)

        if import_data is not None:
            flash_success(_("File imported successfully."))
        else:
            flash_danger(_("Error importing file."))

    copied_record = _get_copied_record(qparams["record"])
    current_template = _get_current_template(qparams["template"])
    linked_collection = _get_linked_collection(qparams["collection"])

    form = NewRecordForm(
        import_data=import_data,
        record=copied_record,
        template=current_template,
        collection=linked_collection,
    )

    if request.method == "POST" and import_type is None:
        if form.validate():
            record = create_record(
                title=form.title.data,
                identifier=form.identifier.data,
                type=form.type.data,
                description=form.description.data,
                license=form.license.data,
                visibility=form.visibility.data,
                tags=form.tags.data,
                extras=form.extras.data,
            )

            if record:
                add_links(Collection, record.collections, form.collections.data)
                create_record_links(record, form.record_links.data)
                update_roles(record, form.roles.data)
                db.session.commit()

                flash_success(_("Record created successfully."))

                if form.submit_files.data:
                    return redirect(
                        url_for(
                            "records.add_files", id=record.id, tab=qparams["redirect"]
                        )
                    )

                return redirect(url_for("records.view_record", id=record.id))

        flash_danger(_("Error creating record."))

    if current_template is not None and (
        current_template.type != TemplateType.RECORD or copied_record is not None
    ):
        current_template = None

    return render_template(
        "records/new_record.html",
        title=_("New record"),
        form=form,
        record_template=current_template,
        redirect=qparams["redirect"],
        js_context={"title_field": form.title.to_dict()},
    )


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
@permission_required("update", "record", "id")
@qparam("key", multiple=True)
def edit_record(id, qparams):
    """Page to edit an existing record."""
    record = Record.query.get_active_or_404(id)
    form = EditRecordForm(record)

    if request.method == "POST":
        if form.validate():
            if update_record(
                record,
                title=form.title.data,
                identifier=form.identifier.data,
                type=form.type.data,
                description=form.description.data,
                license=form.license.data,
                visibility=form.visibility.data,
                tags=form.tags.data,
                extras=form.extras.data,
            ):
                flash_success(_("Changes saved successfully."))

                if form.submit_quit.data:
                    return redirect(url_for("records.view_record", id=record.id))

                return redirect(url_for("records.edit_record", id=record.id))

        flash_danger(_("Error editing record."))

    return render_template(
        "records/edit_record.html",
        title=_("Edit record"),
        form=form,
        record=record,
        js_context={
            "title_field": form.title.to_dict(),
            "edit_extra_keys": qparams["key"],
        },
    )


def _view_record(record, qparams):
    schema = RecordSchema(only=["id", "title", "identifier"])

    current_collection = None
    prev_record = None
    next_record = None

    # Set up a collection as context based on a query parameter or the session. The
    # latter requires the user to not have navigated to another record in the meantime.
    if collection_id := qparams["collection"]:
        current_collection = Collection.query.get(collection_id)
    elif (
        context := session.get(const.SESSION_KEY_COLLECTION_CONTEXT)
    ) is not None and context["record"] == record.id:
        current_collection = Collection.query.get(context["collection"])

    if current_collection is not None and has_permission(
        current_user, "read", "collection", current_collection.id
    ):
        prev_record = (
            get_linked_resources(Record, current_collection.records)
            .filter(Record.last_modified > record.last_modified)
            .order_by(Record.last_modified)
            .first()
        )
        next_record = (
            get_linked_resources(Record, current_collection.records)
            .filter(Record.last_modified < record.last_modified)
            .order_by(Record.last_modified.desc())
            .first()
        )

        session[const.SESSION_KEY_COLLECTION_CONTEXT] = {
            "record": record.id,
            "collection": current_collection.id,
        }
    else:
        session.pop(const.SESSION_KEY_COLLECTION_CONTEXT, None)
        current_collection = None

    return render_template(
        "records/view_record.html",
        record=record,
        current_collection=current_collection,
        prev_record=prev_record,
        next_record=next_record,
        publication_providers=get_publication_providers(record),
        js_context={"record": schema.dump(record)},
    )


@bp.get("/<int:id>")
@permission_required("read", "record", "id")
@qparam("collection", type=const.QPARAM_TYPE_INT, default=None)
def view_record(id, qparams):
    """Page to view a record."""
    record = Record.query.get_active_or_404(id)

    return _view_record(record, qparams)


@bp.get("/identifier/<identifier:identifier>")
@login_required
@qparam("collection", type=const.QPARAM_TYPE_INT, default=None)
def view_record_by_identifier(identifier, qparams):
    """Page to view a record."""
    record = Record.query.filter_by(
        identifier=identifier, state=RecordState.ACTIVE
    ).first_or_404()

    if not has_permission(current_user, "read", "record", record.id):
        return html_error_response(403)

    return _view_record(record, qparams)


def _export_data(record_id, export_type, resource_type, export_endpoint):
    record = Record.query.get_active_or_404(record_id)
    export_types = const.EXPORT_TYPES[resource_type]

    if export_type not in export_types:
        return html_error_response(404)

    return render_template(
        "records/export_record.html",
        title=export_types[export_type]["title"],
        record=record,
        resource_type=resource_type,
        export_type=export_type,
        export_endpoint=url_for(export_endpoint, id=record.id, export_type=export_type),
    )


@bp.get("/<int:id>/export/<export_type>")
@permission_required("read", "record", "id")
def export_record(id, export_type):
    """Page to view the exported data of a record."""
    return _export_data(id, export_type, "record", "api.get_record_export_internal")


@bp.get("/<int:id>/extras/export/<export_type>")
@permission_required("read", "record", "id")
def export_extras(id, export_type):
    """Page to view the exported data of the extras of a record."""
    return _export_data(id, export_type, "extras", "api.get_extras_export")


@bp.route("/<int:id>/publish/<provider>", methods=["GET", "POST"])
@permission_required("read", "record", "id")
def publish_record(id, provider):
    """Page to publish a record using a given provider."""
    record = Record.query.get_active_or_404(id)
    publication_provider = get_publication_provider(provider, record)

    if publication_provider is None:
        return html_error_response(404)

    try:
        form = run_hook("kadi_get_publication_form", provider=provider, resource=record)
    except Exception as e:
        current_app.logger.exception(e)
        form = None

    if request.method == "POST":
        endpoint = url_for("records.view_record", id=record.id)

        if not publication_provider["is_connected"]:
            return redirect(endpoint)

        if form is not None and not form.validate():
            flash_danger(_("Error publishing record."))
        else:
            form_data = form.data if form is not None else None
            status, task = start_publish_resource_task(provider, record, form_data)

            if not status:
                flash_info(_("A publishing task is already in progress."))
            elif task is None:
                flash_danger(_("Error starting publishing task."))
            else:
                flash_success(_("Publishing task started successfully."))

            return redirect(endpoint)

    return render_template(
        "records/publish_record.html",
        title=publication_provider["title"],
        record=record,
        provider=publication_provider,
        form=form,
    )


@bp.route("/<int:id>/links", methods=["GET", "POST"])
@permission_required("link", "record", "id")
@qparam("tab", default="records")
def manage_links(id, qparams):
    """Page to link a record to other records or collections."""
    record = Record.query.get_active_or_404(id)

    record_form = AddRecordLinksForm(suffix="record")
    collections_form = LinkCollectionsForm(suffix="collections")

    if qparams["tab"] == "records" and request.method == "POST":
        if record_form.validate():
            record_links_data = record_form.record_links.data
            num_links_created = create_record_links(record, record_links_data)

            if num_links_created != len(record_links_data):
                # This is the only error that can realistically lead to some links not
                # being created here.
                flash_warning(
                    _("One or more record links already existed and were not created.")
                )

            flash_success(_("Record links created successfully."))
            return redirect(url_for("records.manage_links", id=record.id))

        flash_danger(_("Error creating record links."))

    if qparams["tab"] == "collections" and collections_form.validate_on_submit():
        add_links(Collection, record.collections, collections_form.collections.data)
        db.session.commit()

        flash_success(_("Changes saved successfully."))

    return render_template(
        "records/manage_links.html",
        title=_("Manage links"),
        record_form=record_form,
        collections_form=collections_form,
        record=record,
    )


@bp.get("/<int:record_id>/links/<int:link_id>")
@permission_required("read", "record", "record_id")
def view_record_link(record_id, link_id):
    """Page to view a record link."""
    record = Record.query.get_active_or_404(record_id)
    record_link = RecordLink.query.get_or_404(link_id)
    linked_record = get_linked_record(record_link, record)

    if linked_record is None:
        abort(404)

    if not has_permission(current_user, "read", "record", linked_record.id):
        abort(403)

    record_changes = get_record_link_changes(record_link)

    return render_template(
        "records/view_record_link.html",
        record=record,
        record_link=record_link,
        record_changes=record_changes,
    )


@bp.route("/<int:record_id>/links/<int:link_id>/edit", methods=["GET", "POST"])
@permission_required("link", "record", "record_id")
def edit_record_link(record_id, link_id):
    """Page to edit an existing record link."""
    record = Record.query.get_active_or_404(record_id)
    record_link = RecordLink.query.get_or_404(link_id)
    linked_record = get_linked_record(record_link, record)

    if linked_record is None:
        abort(404)

    if not has_permission(current_user, "link", "record", linked_record.id):
        abort(403)

    form = EditRecordLinkForm(record_link, record)

    if request.method == "POST":
        if form.validate():
            kwargs = {}

            if record_link.record_from == record:
                kwargs["record_to"] = form.record.data
            else:
                kwargs["record_from"] = form.record.data

            try:
                update_record_link(
                    record_link, name=form.name.data, term=form.term.data, **kwargs
                )

                flash_success(_("Changes saved successfully."))
                return redirect(
                    url_for(
                        "records.view_record_link",
                        record_id=record.id,
                        link_id=record_link.id,
                    )
                )
            except (ValueError, KadiPermissionError) as e:
                flash_danger(str(e))
        else:
            flash_danger(_("Error editing record link."))

    return render_template(
        "records/edit_record_link.html",
        title=_("Edit record link"),
        record=record,
        record_link=record_link,
        form=form,
        js_context={
            "name_field": form.name.to_dict(),
            "term_field": form.term.to_dict(),
        },
    )


@bp.route("/<int:id>/permissions", methods=["GET", "POST"])
@permission_required("permissions", "record", "id")
def manage_permissions(id):
    """Page to manage access permissions of a record."""
    record = Record.query.get_active_or_404(id)
    form = AddRolesForm()

    if form.validate_on_submit():
        update_roles(record, form.roles.data)
        db.session.commit()

        flash_success(_("Changes saved successfully."))
        return redirect(url_for("records.manage_permissions", id=record.id))

    return render_template(
        "records/manage_permissions.html",
        title=_("Manage permissions"),
        form=form,
        record=record,
    )


@bp.get("/<int:id>/files")
@permission_required("update", "record", "id")
@qparam("file")
def add_files(id, qparams):
    """Page to add files to a record."""
    record = Record.query.get_active_or_404(id)

    file_upload_type = None
    current_file = None
    current_file_data = None

    try:
        validate_uuid(qparams["file"])
        current_file = record.active_files.filter(File.id == qparams["file"]).first()
        file_upload_type = get_direct_upload_type(current_file)
    except KadiValidationError:
        pass

    if file_upload_type is not None:
        current_file_data = FileSchema().dump(current_file)

    return render_template(
        "records/add_files.html",
        title=_("Add files"),
        record=record,
        current_file=current_file,
        js_context={
            "upload_endpoint": url_for("api.new_upload", id=record.id),
            "file_type": file_upload_type,
            "current_file": current_file_data,
        },
    )


@bp.get("/<int:record_id>/files/<uuid:file_id>")
@permission_required("read", "record", "record_id")
def view_file(record_id, file_id):
    """Page to view a file of a record."""
    record = Record.query.get_active_or_404(record_id)
    file = record.active_files.filter(File.id == file_id).first_or_404()

    prev_file = (
        record.active_files.filter(File.last_modified > file.last_modified)
        .order_by(File.last_modified)
        .first()
    )
    next_file = (
        record.active_files.filter(File.last_modified < file.last_modified)
        .order_by(File.last_modified.desc())
        .first()
    )

    return render_template(
        "records/view_file.html",
        record=record,
        file=file,
        prev_file=prev_file,
        next_file=next_file,
        js_context={
            "get_file_preview_endpoint": url_for(
                "api.get_file_preview", record_id=record.id, file_id=file.id
            )
        },
    )


@bp.route("/<int:record_id>/files/<uuid:file_id>/edit", methods=["GET", "POST"])
@permission_required("update", "record", "record_id")
def edit_file_metadata(record_id, file_id):
    """Page to edit the metadata of an an existing file of a record."""
    record = Record.query.get_active_or_404(record_id)
    file = record.active_files.filter(File.id == file_id).first_or_404()

    form = EditFileForm(file)

    if form.validate_on_submit():
        if update_file(
            file,
            name=form.name.data,
            mimetype=form.mimetype.data,
            description=form.description.data,
        ):
            flash_success(_("Changes saved successfully."))
            return redirect(
                url_for("records.view_file", record_id=record.id, file_id=file.id)
            )

        flash_danger(_("Error editing file."))

    return render_template(
        "records/edit_file_metadata.html",
        title=_("Edit file"),
        form=form,
        record=record,
        file=file,
    )


@bp.get("/<int:record_id>/revisions/<int:revision_id>")
@permission_required("read", "record", "record_id")
@qparam("compare_latest", type=const.QPARAM_TYPE_BOOL, default=False)
def view_record_revision(record_id, revision_id, qparams):
    """Page to view a specific revision of a record."""
    record = Record.query.get_active_or_404(record_id)
    record_revision = record.revisions.filter(
        Record.revision_class.id == revision_id
    ).first_or_404()

    next_revision = (
        record.revisions.join(Revision)
        .filter(Revision.timestamp > record_revision.timestamp)
        .order_by(Revision.timestamp)
        .first()
    )
    prev_revision = (
        record.revisions.join(Revision)
        .filter(Revision.timestamp < record_revision.timestamp)
        .order_by(Revision.timestamp.desc())
        .first()
    )

    return render_template(
        "records/view_revision.html",
        title=_("Revision"),
        record=record,
        revision=record_revision,
        next_revision=next_revision,
        prev_revision=prev_revision,
        revision_endpoint="records.view_record_revision",
        js_context={"compare_latest": qparams["compare_latest"]},
    )


@bp.get("/<int:record_id>/files/revisions/<int:revision_id>")
@permission_required("read", "record", "record_id")
def view_file_revision(record_id, revision_id):
    """Page to view a specific file revision of a record."""
    record = Record.query.get_active_or_404(record_id)
    file_revision = File.revision_class.query.get_or_404(revision_id)

    if record.id != file_revision.file.record_id:
        return html_error_response(404)

    next_revision = (
        file_revision.file.revisions.join(Revision)
        .filter(Revision.timestamp > file_revision.timestamp)
        .order_by(Revision.timestamp)
        .first()
    )
    prev_revision = (
        file_revision.file.revisions.join(Revision)
        .filter(Revision.timestamp < file_revision.timestamp)
        .order_by(Revision.timestamp.desc())
        .first()
    )

    return render_template(
        "records/view_revision.html",
        title=_("Revision"),
        record=record,
        revision=file_revision,
        next_revision=next_revision,
        prev_revision=prev_revision,
        revision_endpoint="records.view_file_revision",
    )


@bp.post("/<int:id>/delete")
@permission_required("delete", "record", "id")
def delete_record(id):
    """Endpoint to mark an existing record as deleted.

    Works the same as the corresponding API endpoint.
    """
    record = Record.query.get_active_or_404(id)
    _delete_record(record)

    flash_success(_("Record successfully moved to the trash."))
    return redirect(url_for("records.records"))


@bp.post("/<int:record_id>/links/<int:link_id>/delete")
@permission_required("link", "record", "record_id")
def remove_record_link(record_id, link_id):
    """Endpoint to delete an existing record link.

    Works the same as the corresponding API endpoint.
    """
    record = Record.query.get_active_or_404(record_id)
    record_link = RecordLink.query.get_or_404(link_id)
    linked_record = get_linked_record(record_link, record)

    if linked_record is None:
        abort(404)

    if not has_permission(current_user, "link", "record", linked_record.id):
        abort(403)

    try:
        _remove_record_link(record_link)
        flash_success(_("Record link removed successfully."))
    except KadiPermissionError:
        pass

    return redirect(url_for("records.view_record", id=record.id, tab="links"))


@bp.post("/<int:record_id>/files/<uuid:file_id>/delete")
@permission_required("update", "record", "record_id")
def delete_file(record_id, file_id):
    """Endpoint to delete an existing file.

    Works the same as the corresponding API endpoint.
    """
    record = Record.query.get_active_or_404(record_id)
    file = record.active_files.filter(File.id == file_id).first_or_404()

    _delete_file(file)

    flash_success(_("File deleted successfully."))
    return redirect(url_for("records.view_record", id=record.id, tab="files"))
