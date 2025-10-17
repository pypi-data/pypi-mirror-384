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

import kadi.lib.constants as const
from kadi.lib.db import escape_like
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.tags.models import Tag
from kadi.modules.collections.models import Collection
from kadi.modules.records.models import Record

from .models import Tag


def get_tags(filter_term="", resource_type=None, user=None):
    """Get all distinct tags of resources a user can access.

    :param filter_term: (optional) A (case insensitive) term to filter the tags by their
        name.
    :param resource_type: (optional) A resource type to limit the tags to. One of
        ``"record"`` or ``"collection"``.
    :param user: (optional) The user who will be checked for access permissions.
        Defaults to the current user.
    :return: The tags as query, ordered by their name in ascending order.
    """
    user = user if user is not None else current_user

    if resource_type == "record":
        models = [Record]
    elif resource_type == "collection":
        models = [Collection]
    else:
        models = [Record, Collection]

    tags_queries = []

    for model in models:
        tags_query = Tag.query.join(model.tags).filter(
            model.state == const.MODEL_STATE_ACTIVE,
            model.id.in_(
                get_permitted_objects(user, "read", model.__tablename__).with_entities(
                    model.id
                )
            ),
        )
        tags_queries.append(tags_query)

    tags_query = (
        tags_queries[0]
        .union(*tags_queries[1:])
        .filter(Tag.name.ilike(f"%{escape_like(filter_term)}%"))
        .distinct()
        .order_by(Tag.name)
    )

    return tags_query
