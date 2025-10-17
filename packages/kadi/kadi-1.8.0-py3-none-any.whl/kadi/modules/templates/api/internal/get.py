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
from flask_login import login_required

import kadi.lib.constants as const
from kadi.lib.api.blueprint import bp
from kadi.lib.api.core import internal
from kadi.lib.conversion import normalize
from kadi.lib.resources.api import get_selected_resources
from kadi.lib.web import qparam
from kadi.modules.templates.models import Template


@bp.get("/templates/select")
@login_required
@internal
@qparam("page", type=const.QPARAM_TYPE_INT, default=1)
@qparam("term", parse=normalize)
@qparam("type", multiple=True)
def select_templates(qparams):
    """Search templates in dynamic selections.

    Similar to :func:`kadi.lib.resources.api.get_selected_resources`.
    """
    filters = []

    if template_type := qparams["type"]:
        filters.append(Template.type.in_(template_type))

    return get_selected_resources(
        Template, page=qparams["page"], filter_term=qparams["term"], filters=filters
    )
