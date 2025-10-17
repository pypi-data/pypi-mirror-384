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
from flask import redirect
from flask import render_template
from flask import request
from flask_babel import format_number
from flask_babel import gettext as _
from flask_login import current_user

from kadi.ext.db import db
from kadi.lib.db import get_disk_space
from kadi.lib.format import filesize
from kadi.lib.mails.utils import send_test_mail
from kadi.lib.security import random_alnum
from kadi.lib.utils import utcnow
from kadi.lib.web import flash_danger
from kadi.lib.web import flash_success
from kadi.lib.web import qparam
from kadi.lib.web import url_for
from kadi.modules.accounts.forms import CreateLocalUserForm
from kadi.modules.accounts.models import User
from kadi.modules.accounts.models import UserState
from kadi.modules.accounts.providers import LocalProvider
from kadi.modules.accounts.tasks import start_merge_users_task
from kadi.modules.collections.models import Collection
from kadi.modules.collections.models import CollectionState
from kadi.modules.groups.models import Group
from kadi.modules.groups.models import GroupState
from kadi.modules.records.models import File
from kadi.modules.records.models import FileState
from kadi.modules.records.models import Record
from kadi.modules.records.models import RecordState
from kadi.modules.sysadmin.forms import MergeUsersForm
from kadi.modules.templates.models import Template
from kadi.modules.templates.models import TemplateState

from .blueprint import bp
from .forms import CustomizationConfigForm
from .forms import LegalsConfigForm
from .forms import MiscConfigForm
from .utils import delete_index_image
from .utils import save_index_image
from .utils import sysadmin_required


@bp.get("")
@sysadmin_required
def view_information():
    """Page for sysadmins to view various information."""
    num_users = User.query.filter(
        User.state == UserState.ACTIVE,
        User.new_user_id.is_(None),
    ).count()
    num_records = Record.query.filter(
        Record.state == RecordState.ACTIVE,
    ).count()
    num_collections = Collection.query.filter(
        Collection.state == CollectionState.ACTIVE,
    ).count()
    num_templates = Template.query.filter(
        Template.state == TemplateState.ACTIVE,
    ).count()
    num_groups = Group.query.filter(
        Group.state == GroupState.ACTIVE,
    ).count()

    files_query = File.query.filter(File.state == FileState.ACTIVE)
    file_size = files_query.with_entities(db.func.sum(File.size)).scalar() or 0

    stats = {
        "db_size": filesize(get_disk_space()),
        "num_users": format_number(num_users),
        "num_records": format_number(num_records),
        "num_collections": format_number(num_collections),
        "num_templates": format_number(num_templates),
        "num_groups": format_number(num_groups),
        "num_files": format_number(files_query.count()),
        "file_size": filesize(file_size),
    }

    return render_template(
        "sysadmin/view_information.html",
        title=_("Information"),
        stats=stats,
        js_context={
            "get_system_information_endpoint": url_for("api.get_system_information"),
            "server_time": utcnow().isoformat(),
        },
    )


@bp.route("/config", methods=["GET", "POST"])
@sysadmin_required
@qparam("tab", default="customization")
@qparam("action")
def manage_config(qparams):
    """Page for sysadmins to manage global config items."""
    save_changes = False

    customization_form = CustomizationConfigForm(suffix="customization")
    legals_form = LegalsConfigForm(suffix="legals")
    misc_form = MiscConfigForm(suffix="misc")

    if qparams["tab"] == "customization" and customization_form.validate_on_submit():
        save_changes = True
        customization_form.set_config_values()

        if customization_form.remove_image.data:
            delete_index_image()
        elif customization_form.index_image.data:
            save_index_image(request.files[customization_form.index_image.name])

    elif qparams["tab"] == "legals" and legals_form.validate_on_submit():
        save_changes = True
        legals_form.set_config_values()

        # Always accept the (potentially updated) legal notices automatically for the
        # current user.
        current_user.accept_legals()

    elif qparams["tab"] == "misc" and request.method == "POST":
        if qparams["action"] == "test_email":
            if send_test_mail(current_user):
                flash_success(_("A test email has been sent."))
            else:
                flash_danger(_("Could not send test email."))

            return redirect(url_for("sysadmin.manage_config", tab=qparams["tab"]))

        if misc_form.validate():
            save_changes = True
            misc_form.set_config_values()

    if save_changes:
        db.session.commit()

        flash_success(_("Changes saved successfully."))
        return redirect(url_for("sysadmin.manage_config", tab=qparams["tab"]))

    return render_template(
        "sysadmin/manage_config.html",
        title=_("Configuration"),
        customization_form=customization_form,
        legals_form=legals_form,
        misc_form=misc_form,
    )


@bp.route("/users", methods=["GET", "POST"])
@qparam("tab", default="manage")
@sysadmin_required
def manage_users(qparams):
    """Page for sysadmins to manage users."""
    new_username = None
    new_password = None
    local_provider_registered = LocalProvider.is_registered()

    merge_users_form = MergeUsersForm(suffix="merge")
    register_user_form = CreateLocalUserForm(suffix="register")

    if qparams["tab"] == "merge" and merge_users_form.validate_on_submit():
        primary_user = User.query.get_active(merge_users_form.primary_user.data)
        secondary_user = User.query.get_active(merge_users_form.secondary_user.data)

        if (
            primary_user is not None
            and secondary_user is not None
            and primary_user != secondary_user
            and start_merge_users_task(primary_user, secondary_user)
        ):
            flash_success(_("User merge triggered successfully."))
            return redirect(url_for("sysadmin.manage_users", tab="merge"))

        flash_danger(_("Error merging users."))

    elif (
        qparams["tab"] == "register"
        and local_provider_registered
        and request.method == "POST"
    ):
        if register_user_form.validate():
            new_username = register_user_form.username.data
            new_password = random_alnum()

            if LocalProvider.register(
                displayname=register_user_form.displayname.data,
                email=register_user_form.email.data,
                username=new_username,
                password=new_password,
            ):
                flash_success(_("User created successfully."))

                # Manually clear the form, as redirecting would also clear the generated
                # password value.
                register_user_form = CreateLocalUserForm(
                    suffix="register", formdata=None
                )
            else:
                flash_danger(_("Error registering user."))
                return redirect(url_for("sysadmin.manage_users", tab="register"))
        else:
            flash_danger(_("Error registering user."))

    return render_template(
        "sysadmin/manage_users.html",
        title=_("User management"),
        merge_users_form=merge_users_form,
        register_user_form=register_user_form,
        local_provider_registered=local_provider_registered,
        new_username=new_username,
        new_password=new_password,
    )
