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
from datetime import timedelta

from elasticsearch.dsl import Q as Query
from flask import current_app
from flask_login import current_user

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.permissions.core import get_permitted_objects
from kadi.lib.resources.utils import get_filtered_resources
from kadi.lib.resources.utils import search_resources
from kadi.lib.tags.models import Tag
from kadi.lib.utils import is_quoted
from kadi.lib.utils import utcnow
from kadi.modules.collections.models import Collection
from kadi.modules.collections.models import CollectionState
from kadi.modules.collections.utils import get_child_collections

from .files import remove_file
from .models import File
from .models import FileState
from .models import Record
from .models import Upload
from .models import UploadState
from .uploads import remove_upload


def search_records(
    search_query=None,
    page=1,
    per_page=10,
    sort="_score",
    visibility=None,
    explicit_permissions=False,
    user_ids=None,
    collection_ids=None,
    child_collections=False,
    record_types=None,
    tags=None,
    tag_operator="or",
    mimetypes=None,
    extras=None,
    user=None,
):
    """Search for and filter records.

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
    :param collection_ids: (optional) A list of collection IDs the searched records need
        to belong to.
    :param child_collections: (optional) Flag indicating whether the records of the
        children of the given collection IDs should be included.
    :param record_types: (optional) A list of record types to filter the records with.
    :param tags: (optional) A list of tag names to filter the records with.
    :param tag_operator: (optional) The operator to filter the tags with. One of
        ``"or"`` or ``"and"``.
    :param mimetypes: (optional) A list of MIME types to filter the records with based
        on their files
    :param extras: (optional) A list of dictionaries to specifiy search queries within
        the extra metadata of records. Each query can contain a link operator, a key, a
        type and one or multiple value restrictions depending on the type. See also
        :attr:`.Record.extras`.

        **Example:**

        .. code-block:: python3

            [
                {
                    # The link operator, one of "and" or "or". Note that the operator of
                    # the first query can also be left out and that the "and" operator
                    # has a higher precedence.
                    "link": "and",
                    # The key of the metadatum. Supports exact matches when surrounded
                    # by double quotes. Note that nested keys are indexed in the form of
                    # "key_1.key_2". Within lists, keys are replaced by the
                    # corresponding index in the list instead, starting at 1.
                    "key": "sample key",
                    # The type of the metadatum, one of "str", "numeric" (for integer
                    # and float values), "bool" or "date".
                    "type": "str",
                    # The string value of the metadatum if the type is "str". Supports
                    # exact matches when surrounded by double quotes.
                    "str": "string",
                    # Restrictions about the numeric value of the metadatum if the type
                    # is "numeric". Either a minimum value ("min"), a maximum value
                    # ("max") or both can be specified. Note that the range is always
                    # inclusive. Units ("unit") can optionally be specified as well and
                    # are always matched exactly.
                    "numeric": {"min": 0, "max": 1, "unit": "cm"},
                    # The boolean value of the metadatum if the type is "bool", one of
                    # True, "true", False or "false".
                    "bool": True,
                    # Restrictions about the date value of the metadatum if the type is
                    # "date". Either a minimum value ("min"), a maximum value ("max") or
                    # both can be specified as a formatted date string. Note that the
                    # range is always inclusive.
                    "date": {
                        "min": "2020-07-01T00:00:00.000Z",
                        "max": "2020-07-02T00:00:00.000Z",
                    },
                },
            ]
    :param user: (optional) The user to check for any permissions regarding the searched
        records. Defaults to the current user.
    :return: The search results as returned by
        :func:`kadi.lib.resources.utils.search_resources`.
    """
    user = user if user is not None else current_user

    records_query = get_filtered_resources(
        Record,
        visibility=visibility,
        explicit_permissions=explicit_permissions,
        user_ids=user_ids,
        user=user,
    )

    if collection_ids:
        collections_query = get_permitted_objects(user, "read", "collection").filter(
            Collection.state == CollectionState.ACTIVE,
            Collection.id.in_(collection_ids),
        )

        if child_collections:
            child_collection_ids = []

            for collection in collections_query:
                child_collection_ids += [
                    c.id for c in get_child_collections(collection)
                ]

            collections_query = collections_query.union(
                Collection.query.filter(Collection.id.in_(child_collection_ids))
            )

        records_query = records_query.join(Record.collections).filter(
            Collection.id.in_(collections_query.with_entities(Collection.id))
        )

    if record_types:
        records_query = records_query.filter(Record.type.in_(record_types))

    if tags:
        if tag_operator == "and":
            tag_filters = []

            for tag in tags:
                tag_filters.append(Record.tags.any(Tag.name == tag))

            records_query = records_query.filter(*tag_filters)
        else:
            # Always fall back to "or" otherwise.
            records_query = records_query.join(Record.tags).filter(Tag.name.in_(tags))

    if mimetypes:
        records_query = records_query.join(File).filter(
            File.state == FileState.ACTIVE, File.mimetype.in_(mimetypes)
        )

    record_ids = [r.id for r in records_query.with_entities(Record.id)]

    # Construct an Elasticsearch DSL query object for the extra queries, if applicable.
    extra_es_query = None

    if extras:
        or_relations = []
        and_relations = []

        # Multiple queries with different link operators are effectively combined as:
        # (Q1 AND Q2) OR (Q3 AND Q4). Note that the first link operator does not
        # actually matter.
        for extra_query in extras:
            es_query = _extras_dict_to_query(extra_query)

            if es_query:
                if extra_query.get("link") == "or":
                    if and_relations:
                        or_relations.append(Query("bool", must=and_relations))

                    and_relations = [es_query]
                else:
                    and_relations.append(es_query)

        or_relations.append(Query("bool", must=and_relations))
        extra_es_query = Query("bool", should=or_relations)

    return search_resources(
        Record,
        search_query=search_query,
        page=page,
        per_page=per_page,
        sort=sort,
        filter_ids=record_ids,
        extra_es_query=extra_es_query,
    )


def _make_extra_key_query(extra_type, extra_key, nested=False):
    should_query = []

    if is_quoted(extra_key):
        extra_key = extra_key[1:-1]
    else:
        if len(extra_key) < 3:
            # For very short queries (i.e. smaller than the indexed trigrams), perform a
            # prefix query instead.
            query = Query(
                "prefix", **{f"extras_{extra_type}.key": {"value": extra_key}}
            )
        else:
            query = Query(
                "match",
                **{
                    f"extras_{extra_type}.key": {
                        "query": extra_key,
                        "fuzziness": "AUTO",
                    }
                },
            )

        if not nested:
            should_query.append(query)
        else:
            should_query.append(
                Query("nested", path=f"extras_{extra_type}", query=query)
            )

    # Always perform a term query with a higher weight.
    term_query = Query(
        "term", **{f"extras_{extra_type}.key.keyword": {"value": extra_key, "boost": 5}}
    )

    if not nested:
        should_query.append(term_query)
    else:
        should_query.append(
            Query("nested", path=f"extras_{extra_type}", query=term_query)
        )

    return Query("bool", should=should_query)


def _extras_dict_to_query(query_dict):
    extra_type = str(query_dict.get("type", ""))
    extra_key = str(query_dict.get("key", ""))

    # Build a query for a single string value and its key.
    if extra_type == "str":
        str_query = []
        str_value = str(query_dict.get("str", ""))

        if str_value:
            should_query = []

            if is_quoted(str_value):
                str_value = str_value[1:-1]
            else:
                if len(str_value) < 3:
                    # For very short queries (i.e. smaller than the indexed trigrams),
                    # perform a prefix query instead.
                    should_query.append(
                        Query("prefix", extras_str__value={"value": str_value})
                    )
                else:
                    should_query.append(
                        Query(
                            "match",
                            extras_str__value={"query": str_value, "fuzziness": "AUTO"},
                        )
                    )

            # Always perform a term query with a higher weight.
            should_query.append(
                Query(
                    "term", extras_str__value__keyword={"value": str_value, "boost": 5}
                )
            )
            str_query.append(Query("bool", should=should_query))

        if extra_key:
            str_query.append(_make_extra_key_query("str", extra_key))

        return Query("nested", path="extras_str", query=Query("bool", must=str_query))

    # Build a query for a single numeric value and its key.
    if extra_type == "numeric":
        int_query = []
        float_query = []

        numeric_dict = query_dict.get("numeric")

        if not isinstance(numeric_dict, dict):
            numeric_dict = {}

        min_value = str(numeric_dict.get("min", ""))
        max_value = str(numeric_dict.get("max", ""))
        unit_value = str(numeric_dict.get("unit", ""))

        if min_value:
            int_query.append(Query("range", extras_int__value={"gte": min_value}))
            float_query.append(Query("range", extras_float__value={"gte": min_value}))

        if max_value:
            int_query.append(Query("range", extras_int__value={"lte": max_value}))
            float_query.append(Query("range", extras_float__value={"lte": max_value}))

        if unit_value:
            int_query.append(Query("match", extras_int__unit=unit_value))
            float_query.append(Query("match", extras_float__unit=unit_value))

        if extra_key:
            int_query.append(_make_extra_key_query("int", extra_key))
            float_query.append(_make_extra_key_query("float", extra_key))

        return Query(
            "bool",
            should=[
                Query("nested", path="extras_int", query=Query("bool", must=int_query)),
                Query(
                    "nested", path="extras_float", query=Query("bool", must=float_query)
                ),
            ],
        )

    # Build a query for a single bool value and its key.
    if extra_type == "bool":
        bool_query = []
        bool_value = str(query_dict.get("bool", ""))

        if bool_value.lower() == "true":
            bool_query.append(Query("term", extras_bool__value=True))
        elif bool_value.lower() == "false":
            bool_query.append(Query("term", extras_bool__value=False))

        if extra_key:
            bool_query.append(_make_extra_key_query("bool", extra_key))

        return Query("nested", path="extras_bool", query=Query("bool", must=bool_query))

    # Build a query for a single date value and its key.
    if extra_type == "date":
        date_query = []

        date_dict = query_dict.get("date")

        if not isinstance(date_dict, dict):
            date_dict = {}

        min_value = str(date_dict.get("min", ""))
        max_value = str(date_dict.get("max", ""))

        if min_value:
            date_query.append(Query("range", extras_date__value={"gte": min_value}))

        if max_value:
            date_query.append(Query("range", extras_date__value={"lte": max_value}))

        if extra_key:
            date_query.append(_make_extra_key_query("date", extra_key))

        return Query("nested", path="extras_date", query=Query("bool", must=date_query))

    # Build a query for a key of any type.
    if extra_key:
        return Query(
            "bool",
            should=[
                _make_extra_key_query(extra_type, extra_key, nested=True)
                for extra_type in ["str", "int", "float", "bool", "date"]
            ],
        )

    return None


def get_user_quota(user=None):
    """Get the total size (quota) of a user's files and uploads.

    All active files as well as active and processing uploads are taken into account.
    Uploads that replace files are only considered if their size is larger than the file
    they are replacing, in which case the size difference between the upload and the
    replaced file is added to the total. Note that if multiple uploads replace the same
    file, their combined size is taken instead.

    :param user: (optional) The user to calculate the quota for. Defaults to the current
        user.
    :return: The user's quota.
    """
    user = user if user is not None else current_user

    # Calculate the total size of all active files of the user.
    total_size = (
        user.files.filter(File.state == FileState.ACTIVE)
        .with_entities(db.func.sum(File.size))
        .scalar()
    ) or 0

    uploads_query = user.uploads.filter(
        Upload.state.in_([UploadState.ACTIVE, UploadState.PROCESSING]),
    )

    # Calculate and add the size of all new active and processing uploads of the user to
    # the total.
    total_size += (
        uploads_query.filter(Upload.file_id.is_(None))
        .with_entities(db.func.sum(Upload.size))
        .scalar()
    ) or 0

    # For all active and processing uploads that replace a file, retrieve the combined
    # upload size per replaced file and add the difference to the total if its larger
    # than the size of the replaced file.
    for upload in (
        uploads_query.filter(Upload.file_id.is_not(None))
        .with_entities(Upload.file_id, db.func.sum(Upload.size).label("total_size"))
        .group_by(Upload.file_id)
    ):
        file = (
            File.query.filter(File.id == upload.file_id)
            .with_entities(File.size)
            .first()
        )
        total_size += max(upload.total_size - file.size, 0)

    return total_size


def clean_files(inside_task=False):
    """Clean all expired/inactive files and uploads.

    Note that this function may issue one or more database commits.

    :param inside_task: (optional) A flag indicating whether the function is executed in
        a task. In that case, additional information will be logged.
    """

    # Remove expired inactive files.
    expiration_date = utcnow() - timedelta(seconds=const.INACTIVE_FILES_MAX_AGE)
    files = File.query.filter(
        File.state == FileState.INACTIVE, File.last_modified < expiration_date
    )

    if inside_task and files.count() > 0:
        current_app.logger.info(f"Cleaning {files.count()} inactive file(s).")

    for file in files:
        remove_file(file, delete_from_db=False)

    # Remove expired and inactive uploads.
    active_expiration_date = utcnow() - timedelta(seconds=const.ACTIVE_UPLOADS_MAX_AGE)
    inactive_expiration_date = utcnow() - timedelta(
        seconds=const.INACTIVE_UPLOADS_MAX_AGE
    )

    uploads = Upload.query.filter(
        db.or_(
            db.and_(
                Upload.state == UploadState.ACTIVE,
                Upload.last_modified < active_expiration_date,
            ),
            db.and_(
                Upload.state == UploadState.INACTIVE,
                Upload.last_modified < inactive_expiration_date,
            ),
        )
    )

    if inside_task and uploads.count() > 0:
        current_app.logger.info(
            f"Cleaning {uploads.count()} expired or inactive upload(s)."
        )

    for upload in uploads:
        remove_upload(upload)
