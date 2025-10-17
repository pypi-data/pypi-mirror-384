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
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import add_role
from kadi.lib.resources.schemas import GroupResourceRoleSchema
from kadi.lib.resources.schemas import UserResourceRoleSchema
from kadi.modules.accounts.models import User
from kadi.modules.groups.models import Group
from kadi.modules.templates.core import create_template
from kadi.modules.templates.core import purge_template as _purge_template
from kadi.modules.templates.core import restore_template as _restore_template
from kadi.modules.templates.models import Template
from kadi.modules.templates.models import TemplateState
from kadi.modules.templates.schemas import TemplateSchema


@bp.post("/templates")
@permission_required("create", "template", None)
@scopes_required("template.create")
@reqschema(
    TemplateSchema(exclude=["id"]),
    description="The metadata and data of the new template, depending on its type.",
)
@status(201, "Return the new template.")
def new_template(schema):
    """Create a new template."""
    template = create_template(**schema.load_or_400())

    if not template:
        return json_error_response(409, description="Error creating template.")

    return json_response(201, TemplateSchema().dump(template))


@bp.post("/templates/<int:id>/roles/users")
@permission_required("permissions", "template", "id")
@scopes_required("template.permissions")
@reqschema(
    UserResourceRoleSchema(only=["user.id", "role.name"]),
    description="The user and corresponding role to add.",
)
@status(201, "User role successfully added to template.")
@status(409, "A role for that user already exists.")
def add_template_user_role(id, schema):
    """Add a user role to the template specified by the given ID."""
    template = Template.query.get_active_or_404(id)
    data = schema.load_or_400()
    user = User.query.get_active_or_404(data["user"]["id"])

    if user.is_merged:
        return json_error_response(404)

    return add_role(user, template, data["role"]["name"])


@bp.post("/templates/<int:id>/roles/groups")
@permission_required("permissions", "template", "id")
@scopes_required("template.permissions")
@reqschema(
    GroupResourceRoleSchema(only=["group.id", "role.name"]),
    description="The group and corresponding role to add.",
)
@status(201, "Group role successfully added to template.")
@status(409, "A role for that group already exists.")
def add_template_group_role(id, schema):
    """Add a group role to the template specified by the given ID."""
    template = Template.query.get_active_or_404(id)
    data = schema.load_or_400()
    group = Group.query.get_active_or_404(data["group"]["id"])

    return add_role(group, template, data["role"]["name"])


@bp.post("/templates/<int:id>/restore")
@login_required
@scopes_required("misc.manage_trash")
@status(200, "Return the restored template.")
def restore_template(id):
    """Restore the deleted template specified by the given ID.

    Only the creator of a template can restore it.
    """
    template = Template.query.get_or_404(id)

    if template.state != TemplateState.DELETED or template.creator != current_user:
        return json_error_response(404)

    _restore_template(template)
    db.session.commit()

    return json_response(200, TemplateSchema().dump(template))


@bp.post("/templates/<int:id>/purge")
@login_required
@scopes_required("misc.manage_trash")
@status(204, "Template purged successfully.")
def purge_template(id):
    """Purge the deleted template specified by the given ID.

    Will remove the template permanently. Only the creator of a template can purge it.
    """
    template = Template.query.get_or_404(id)

    if template.state != TemplateState.DELETED or template.creator != current_user:
        return json_error_response(404)

    _purge_template(template)
    db.session.commit()

    return json_response(204)
