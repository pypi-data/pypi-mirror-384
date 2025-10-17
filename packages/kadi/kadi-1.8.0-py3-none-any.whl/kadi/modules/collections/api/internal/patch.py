# Copyright 2022 Karlsruhe Institute of Technology
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
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import internal
from kadi.lib.permissions.utils import permission_required
from kadi.lib.resources.api import toggle_favorite_resource
from kadi.modules.collections.models import Collection


@bp.patch("/collections/<int:id>/favorite")
@permission_required("read", "collection", "id")
@internal
def toggle_favorite_collection(id):
    """Toggle the favorite state of a collection."""
    collection = Collection.query.get_active_or_404(id)
    return toggle_favorite_resource(collection)
