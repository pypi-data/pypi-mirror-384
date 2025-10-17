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

from flask_login import current_user

from kadi.lib.resources.utils import get_filtered_resources
from kadi.lib.resources.utils import search_resources

from .models import Template
from .models import TemplateType


def search_templates(
    search_query=None,
    page=1,
    per_page=10,
    sort="_score",
    visibility=None,
    explicit_permissions=False,
    user_ids=None,
    template_type=None,
    user=None,
):
    """Search and filter for templates.

    Uses :func:`kadi.lib.resources.utils.get_filtered_resources` and
    :func:`kadi.lib.resources.utils.search_resources`.

    :param search_query: (optional) See
        :func:`kadi.lib.resources.utils.search_resources`.
    :param page: (optional) See :func:`kadi.lib.resources.utils.search_resources`.
    :param per_page: (optional) See :func:`kadi.lib.resources.utils.search_resources`.
    :param sort: (optional) See :func:`kadi.lib.resources.utils.search_resources`.
    :param visibility: (optional) See
        :func:`kadi.lib.resources.utils.get_filtered_resources`.
    :param explicit_permissions: (optional) See
        :func:`kadi.lib.resources.utils.get_filtered_resources`.
    :param user_ids: (optional) See
        :func:`kadi.lib.resources.utils.get_filtered_resources`.
    :param template_type: (optional) A type value to filter the templates with.
    :param user: (optional) The user to check for any permissions regarding the searched
        templates. Defaults to the current user.
    :return: The search results as returned by
        :func:`kadi.lib.resources.utils.search_resources`.
    """
    user = user if user is not None else current_user

    templates_query = get_filtered_resources(
        Template,
        visibility=visibility,
        explicit_permissions=explicit_permissions,
        user_ids=user_ids,
        user=user,
    )

    if template_type in TemplateType.__values__:
        templates_query = templates_query.filter(Template.type == template_type)

    template_ids = [t.id for t in templates_query.with_entities(Template.id)]

    return search_resources(
        Template,
        search_query=search_query,
        page=page,
        per_page=per_page,
        sort=sort,
        filter_ids=template_ids,
    )
