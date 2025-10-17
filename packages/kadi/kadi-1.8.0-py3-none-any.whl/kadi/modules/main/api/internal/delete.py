# Copyright 2023 Karlsruhe Institute of Technology
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
from kadi.lib.api.core import internal
from kadi.lib.api.core import json_error_response
from kadi.lib.api.core import json_response
from kadi.lib.notifications.core import dismiss_notification as _dismiss_notification
from kadi.lib.notifications.models import Notification
from kadi.lib.resources.tasks import start_purge_resources_task
from kadi.lib.search.models import SavedSearch


@bp.delete("/notifications/<int:id>")
@login_required
@internal
def dismiss_notification(id):
    """Dismiss a notification of the current user."""
    notification = current_user.notifications.filter(
        Notification.id == id
    ).first_or_404(id)

    _dismiss_notification(notification)
    db.session.commit()

    return json_response(204)


@bp.delete("/saved-searches/<int:id>")
@login_required
@internal
def remove_saved_search(id):
    """Remove a saved search of the current user."""
    saved_search = current_user.saved_searches.filter(
        SavedSearch.id == id
    ).first_or_404()

    db.session.delete(saved_search)
    db.session.commit()

    return json_response(204)


@bp.delete("/trash")
@login_required
@internal
def empty_trash():
    """Empty the trash of the current user."""
    status, task = start_purge_resources_task()

    if not status:
        return json_error_response(429)
    if task is None:
        return json_error_response(503)

    return json_response(202)
