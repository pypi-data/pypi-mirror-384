# Copyright 2025 Karlsruhe Institute of Technology
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
import requests
from flask import current_app
from flask import render_template

from kadi.lib.conversion import truncate

from .constants import TYPE_COLOR_MAP


def search_terms(endpoint, query, page, per_page):
    """Search terms using the given endpoint and query parameters."""
    params = {
        # Specifying an empty query will lead to no results otherwise.
        "q": query or "*",
        "type": ["class", "property", "individual"],
        "fieldList": ["iri", "label", "description", "type"],
        "queryFields": ["label", "synonym", "description", "iri"],
        "groupField": "true",
        "rows": per_page,
        "start": (page - 1) * per_page,
    }

    headers = {"caller": "KADI"}

    response = requests.get(endpoint, params=params, headers=headers, timeout=10)

    if not response.ok:
        current_app.logger.debug(
            f"Invalid response from TIB terminology service ({response.status_code})."
        )
        return None

    data = response.json()["response"]
    items = []

    for item in data["docs"]:
        term = item["iri"]
        item_type = item["type"]
        description = ""

        # Descriptions are wrapped in a (potentially empty) list with a single entry,
        # but we try to be flexible in case this changes in the future.
        if (descriptions := item.get("description")) is not None:
            if isinstance(descriptions, list):
                description = descriptions[0] if len(descriptions) > 0 else ""
            else:
                description = descriptions

            description = truncate(description, 350)

        items.append(
            {
                "term": term,
                "body": render_template(
                    "tib_ts/term.html",
                    term=term,
                    label=item["label"],
                    description=description,
                    type=item_type,
                    type_color=TYPE_COLOR_MAP.get(item_type, "secondary"),
                ),
            }
        )

    return data["numFound"], items
