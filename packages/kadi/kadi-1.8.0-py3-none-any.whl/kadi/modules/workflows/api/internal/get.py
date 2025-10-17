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
from kadi.lib.api.core import json_response
from kadi.lib.api.utils import create_pagination_data
from kadi.lib.conversion import normalize
from kadi.lib.web import paginated
from kadi.lib.web import qparam
from kadi.modules.records.files import get_permitted_files
from kadi.modules.records.models import File
from kadi.modules.workflows.core import parse_tool_file
from kadi.modules.workflows.schemas import WorkflowSchema


@bp.get("/workflows")
@login_required
@internal
@paginated
@qparam("filter", parse=normalize)
def get_workflows(page, per_page, qparams):
    """Get workflow files."""
    paginated_files = (
        get_permitted_files(filter_term=qparams["filter"])
        .filter(File.magic_mimetype == const.MIMETYPE_FLOW)
        .order_by(File.last_modified.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    data = {
        "items": WorkflowSchema(many=True).dump(paginated_files),
        **create_pagination_data(paginated_files.total, page, per_page),
    }

    return json_response(200, data)


@bp.get("/workflows/tools/select")
@login_required
@internal
@paginated
@qparam("filter", parse=normalize)
def select_workflow_tools(page, per_page, qparams):
    """Select workflow tool files.

    For use in the experimental workflow editor.
    """
    paginated_files = (
        get_permitted_files(filter_term=qparams["filter"])
        .filter(File.magic_mimetype == const.MIMETYPE_TOOL)
        .order_by(File.name)
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    items = [
        {
            "id": file.id,
            "file": file.name,
            "record": file.record.identifier,
            "tool": parse_tool_file(file),
        }
        for file in paginated_files
    ]
    data = {
        "items": items,
        **create_pagination_data(paginated_files.total, page, per_page),
    }

    return json_response(200, data)
