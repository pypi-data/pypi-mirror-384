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
from flask import redirect
from flask import render_template
from flask import request
from flask_babel import gettext as _
from flask_login import current_user
from flask_login import login_required

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.tasks import start_apply_role_rules_task
from kadi.lib.permissions.utils import create_username_role_rule
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.views import update_roles
from kadi.lib.revisions.models import Revision
from kadi.lib.web import flash_danger
from kadi.lib.web import flash_success
from kadi.lib.web import html_error_response
from kadi.lib.web import qparam
from kadi.lib.web import url_for
from kadi.modules.accounts.models import User
from kadi.modules.groups.models import GroupState

from .blueprint import bp
from .core import create_group
from .core import delete_group as _delete_group
from .core import update_group
from .forms import AddMembersForm
from .forms import AddRulesForm
from .forms import EditGroupForm
from .forms import NewGroupForm
from .models import Group
from .schemas import GroupSchema
from .utils import delete_group_image
from .utils import save_group_image


@bp.get("")
@login_required
@qparam("user", type=const.QPARAM_TYPE_INT, multiple=True)
def groups(qparams):
    """Group overview page.

    Allows users to search and filter for groups or create new ones.
    """
    users = []

    if user_ids := qparams["user"]:
        users_query = User.query.filter(User.id.in_(user_ids))
        users = [(u.id, f"@{u.identity.username}") for u in users_query]

    return render_template(
        "groups/groups.html", title=_("Groups"), js_context={"users": users}
    )


@bp.route("/new", methods=["GET", "POST"])
@permission_required("create", "group", None)
def new_group():
    """Page to create a new group."""
    form = NewGroupForm()

    if request.method == "POST":
        if form.validate():
            group = create_group(
                title=form.title.data,
                identifier=form.identifier.data,
                description=form.description.data,
                visibility=form.visibility.data,
            )

            if group:
                if form.image.data:
                    save_group_image(group, request.files[form.image.name])

                db.session.commit()

                flash_success(_("Group created successfully."))
                return redirect(url_for("groups.view_group", id=group.id))

        flash_danger(_("Error creating group."))

    return render_template(
        "groups/new_group.html",
        title=_("New group"),
        form=form,
        js_context={"title_field": form.title.to_dict()},
    )


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
@permission_required("update", "group", "id")
def edit_group(id):
    """Page to edit an existing group."""
    group = Group.query.get_active_or_404(id)
    form = EditGroupForm(group)

    if request.method == "POST":
        if form.validate():
            if update_group(
                group,
                title=form.title.data,
                identifier=form.identifier.data,
                description=form.description.data,
                visibility=form.visibility.data,
            ):
                if form.remove_image.data:
                    delete_group_image(group)
                elif form.image.data:
                    save_group_image(group, request.files[form.image.name])

                db.session.commit()
                flash_success(_("Changes saved successfully."))

                if form.submit_quit.data:
                    return redirect(url_for("groups.view_group", id=group.id))

                return redirect(url_for("groups.edit_group", id=group.id))

        flash_danger(_("Error editing group."))

    return render_template(
        "groups/edit_group.html",
        title=_("Edit group"),
        form=form,
        group=group,
        js_context={"title_field": form.title.to_dict()},
    )


def _view_group(group):
    schema = GroupSchema(only=["id", "title", "identifier"])

    return render_template(
        "groups/view_group.html", group=group, js_context={"group": schema.dump(group)}
    )


@bp.get("/<int:id>")
@permission_required("read", "group", "id")
def view_group(id):
    """Page to view a group."""
    group = Group.query.get_active_or_404(id)

    return _view_group(group)


@bp.get("/identifier/<identifier:identifier>")
@login_required
def view_group_by_identifier(identifier):
    """Page to view a group."""
    group = Group.query.filter_by(
        identifier=identifier, state=GroupState.ACTIVE
    ).first_or_404()

    if not has_permission(current_user, "read", "group", group.id):
        return html_error_response(403)

    return _view_group(group)


@bp.route("/<int:id>/members", methods=["GET", "POST"])
@permission_required("members", "group", "id")
@qparam("tab", default="members")
def manage_members(id, qparams):
    """Page to manage members or role rules of a group."""
    group = Group.query.get_active_or_404(id)

    members_form = AddMembersForm(suffix="members")
    rules_form = AddRulesForm(suffix="rules")

    if qparams["tab"] == "members" and members_form.validate_on_submit():
        update_roles(group, members_form.roles.data)
        db.session.commit()

        flash_success(_("Changes saved successfully."))
        return redirect(url_for("groups.manage_members", id=group.id))

    if qparams["tab"] == "rules" and rules_form.validate_on_submit():
        role_rule = create_username_role_rule(
            "group",
            group.id,
            rules_form.role.data,
            rules_form.identity_type.data,
            rules_form.username.data,
        )

        if role_rule:
            db.session.commit()
            flash_success(_("Changes saved successfully."))

            if rules_form.retroactive.data:
                if not start_apply_role_rules_task(role_rule=role_rule):
                    flash_danger(_("Could not apply rule retroactively."))

        return redirect(url_for("groups.manage_members", id=group.id, tab="rules"))

    return render_template(
        "groups/manage_members.html",
        title=_("Manage members"),
        members_form=members_form,
        rules_form=rules_form,
        group=group,
    )


@bp.get("/<int:group_id>/revisions/<int:revision_id>")
@permission_required("read", "group", "group_id")
def view_revision(group_id, revision_id):
    """Page to view a specific revision of a group."""
    group = Group.query.get_active_or_404(group_id)
    group_revision = group.revisions.filter(
        Group.revision_class.id == revision_id
    ).first_or_404()

    next_revision = (
        group.revisions.join(Revision)
        .filter(Revision.timestamp > group_revision.timestamp)
        .order_by(Revision.timestamp)
        .first()
    )
    prev_revision = (
        group.revisions.join(Revision)
        .filter(Revision.timestamp < group_revision.timestamp)
        .order_by(Revision.timestamp.desc())
        .first()
    )

    return render_template(
        "groups/view_revision.html",
        title=_("Revision"),
        group=group,
        revision=group_revision,
        next_revision=next_revision,
        prev_revision=prev_revision,
    )


@bp.post("/<int:id>/delete")
@permission_required("delete", "group", "id")
def delete_group(id):
    """Endpoint to mark an existing group as deleted.

    Works the same as the corresponding API endpoint.
    """
    group = Group.query.get_active_or_404(id)
    _delete_group(group)

    flash_success(_("Group successfully moved to the trash."))
    return redirect(url_for("groups.groups"))
