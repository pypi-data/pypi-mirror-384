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
from kadi.lib.api.core import json_response
from kadi.lib.db import update_object
from kadi.lib.search.models import SavedSearch
from kadi.lib.search.schemas import SavedSearchSchema


@bp.patch("/saved-searches/<int:id>")
@login_required
@internal
def edit_saved_search(id):
    """Edit a saved search of the current user."""
    saved_search = current_user.saved_searches.filter(
        SavedSearch.id == id
    ).first_or_404()

    schema = SavedSearchSchema(only=["name", "query_string"], partial=True)

    update_object(saved_search, **schema.load_or_400())
    db.session.commit()

    return json_response(200, SavedSearchSchema().dump(saved_search))
