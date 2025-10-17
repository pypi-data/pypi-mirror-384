# Copyright 2024 Karlsruhe Institute of Technology
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
from io import BytesIO

from flask import current_app
from flask import json

import kadi.lib.constants as const
from kadi.modules.templates.models import TemplateType

from .schemas import RecordImportSchema


def _parse_json_data(import_data):
    try:
        import_data = json.load(import_data)

        if not isinstance(import_data, dict):
            return None

        # Basic check if we are dealing with template data.
        if "data" in import_data:
            template_type = import_data.get("type")

            if template_type == TemplateType.RECORD:
                import_data = import_data["data"]
            elif template_type == TemplateType.EXTRAS:
                import_data = {"extras": import_data["data"]}
            else:
                return None

        # Make sure to use template-based schema validation.
        return RecordImportSchema(is_template=True, partial=True).load(import_data)

    except Exception as e:
        current_app.logger.debug(e, exc_info=True)
        return None


def parse_import_data(stream, import_type):
    """Parse imported record data of a given format.

    :param stream: The import data as a readable binary stream.
    :param import_type: The import type, currently only ``"json"``.
    :return: The imported record data as a dictionary or ``None`` if the data could not
        be parsed. Note that none of the record properties are guaranteed to be present.
    """
    import_data = BytesIO(stream.read(const.IMPORT_MAX_SIZE))

    if import_type == const.IMPORT_TYPE_JSON:
        return _parse_json_data(import_data)

    return None
