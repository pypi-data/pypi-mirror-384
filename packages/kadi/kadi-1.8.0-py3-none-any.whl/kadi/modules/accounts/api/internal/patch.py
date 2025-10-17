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
from kadi.ext.db import db
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import internal
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.permissions.core import set_system_role
from kadi.lib.permissions.schemas import RoleSchema
from kadi.modules.accounts.models import User
from kadi.modules.accounts.models import UserState
from kadi.modules.sysadmin.utils import sysadmin_required


@bp.patch("/users/<int:id>/system-role")
@sysadmin_required
@internal
def change_system_role(id):
    """Change the system role of a user."""
    user = User.query.get_or_404(id)

    if user.is_merged:
        return json_error_response(404)

    if set_system_role(user, RoleSchema().load_or_400()["name"]):
        db.session.commit()
        return json_response(204)

    return json_error_response(400)


@bp.patch("/users/<int:id>/state")
@sysadmin_required
@internal
def toggle_user_state(id):
    """Toggle the state of a user."""
    user = User.query.get_or_404(id)

    if user.is_merged:
        return json_error_response(404)

    if user.state == UserState.ACTIVE:
        user.state = UserState.INACTIVE
    elif user.state == UserState.INACTIVE:
        user.state = UserState.ACTIVE

    db.session.commit()
    return json_response(204)


@bp.patch("/users/<int:id>/sysadmin")
@sysadmin_required
@internal
def toggle_user_sysadmin(id):
    """Toggle the sysadmin status of a user."""
    user = User.query.get_or_404(id)

    if user.is_merged:
        return json_error_response(404)

    user.is_sysadmin = not user.is_sysadmin
    db.session.commit()

    return json_response(204)
