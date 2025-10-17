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
from elasticsearch.dsl import Document
from elasticsearch.dsl import Search
from elasticsearch.dsl import analyzer
from elasticsearch.dsl import tokenizer
from elasticsearch.exceptions import ConnectionError as ESConnectionError
from elasticsearch.exceptions import NotFoundError as ESNotFoundError
from elasticsearch.exceptions import RequestError as ESRequestError
from flask import current_app

from kadi.ext.elasticsearch import es
from kadi.lib.format import timestamp
from kadi.lib.utils import as_list


TRIGRAM_ANALYZER = analyzer(
    "trigram_analyzer",
    tokenizer=tokenizer("trigram", "ngram", min_gram=3, max_gram=3),
    filter=["lowercase"],
)


class BaseMapping(Document):
    """Base class for all search mappings."""

    @classmethod
    def get_attributes(cls):
        """Get a list of all attributes from a mapping class."""
        properties = cls._doc_type.mapping.properties
        return list(properties._params["properties"].keys())

    @classmethod
    def create_document(cls, obj):
        """Create a new document to be indexed in ElasticSearch

        :param obj: The object to be indexed.
        :return: The created document.
        """
        document = cls()
        document.meta.id = obj.id

        for attr in cls.get_attributes():
            if hasattr(obj, attr):
                setattr(document, attr, getattr(obj, attr))

        return document


def create_index(model, force=False):
    """Create a new search index if it does not exist yet.

    The name of the index will be in the form of ``"<tablename>_<timestamp>"``, where
    ``<tablename>`` depends on the given model. An alias ``<tablename>`` pointing to the
    actual index will also be created automatically if it does not exist yet.

    :param model: The model to create the index of. See also :class:`.SearchableMixin`.
    :param force: (optional) Flag indicating whether a new index should be created even
        if one already exists. Note that if an alias already exists it will not be
        updated automatically to point to the new index.
    :return: The name of the newly created or existing index or ``None`` if no new index
        could be created.
    """
    alias = model.__tablename__

    try:
        alias_exists = es.indices.exists(index=alias)

        if alias_exists and not force:
            return list(es.indices.get_alias(index=alias).keys())[0]

        index = f"{alias}_{timestamp(include_micro=True)}"

        mapping_class = model.get_mapping_class()
        mapping_class.init(using=es, index=index)

        if not alias_exists:
            es.indices.put_alias(index=index, name=alias)

        return index

    except Exception as e:
        current_app.logger.exception(e)

    return None


def add_to_index(obj, index=None):
    """Add an object to its corresponding search index.

    :param obj: The object to index. See also :class:`.SearchableMixin`.
    :param index: (optional) The name of an index that should be used instead of the
        alias corresponding to the given object. See also :func:`create_index`.
    :return: ``True`` if the object was indexed successfully, ``False`` otherwise.
    """
    index = index if index is not None else obj.__tablename__

    try:
        # Check if the index actually exists, as it will be created dynamically
        # otherwise (even if dynamic mapping is turned off for newly added fields).
        if not es.indices.exists(index=index):
            return False

        document = obj.get_mapping_class().create_document(obj)
        document.save(using=es, index=index)
    except ESConnectionError as e:
        if not current_app.config["ELASTICSEARCH_ENABLE_FALLBACK"]:
            current_app.logger.exception(e)

        return False
    except Exception as e:
        current_app.logger.exception(e)
        return False

    return True


def remove_from_index(obj, index=None):
    """Remove an object from its corresponding search index.

    :param obj: The object to remove from the index. See also :class:`.SearchableMixin`.
    :param index: (optional) The name of an index that should be used instead of the
        alias corresponding to the given object. See also :func:`create_index`.
    :return: ``True`` if the object was removed successfully, ``False`` otherwise.
    """
    index = index if index is not None else obj.__tablename__
    mapping_class = obj.get_mapping_class()

    try:
        document = mapping_class.get(using=es, index=index, id=obj.id)
        document.delete(using=es)
    except ESNotFoundError:
        pass
    except ESConnectionError as e:
        if not current_app.config["ELASTICSEARCH_ENABLE_FALLBACK"]:
            current_app.logger.exception(e)

        return False
    except Exception as e:
        current_app.logger.exception(e)
        return False

    return True


def search_index(index, query=None, sort="_score", filter_ids=None, start=0, end=10):
    """Query a specific search index.

    :param index: The name of the search index.
    :param query: (optional) The search query in form of an Elasticsearch DSL query
        object.
    :param sort: (optional) The name of a field or a list of multiple fields to sort on.
    :param filter_ids: (optional) A list of IDs to restrict the search results to.
    :param start: (optional) The start index of the results to return.
    :param end: (optional) The end index of the results to return.
    :return: A response object as returned by the Elasticsearch DSL or ``None`` if the
        request returned an error. Note that only the metadata will be returned as part
        of the search results, without any field data.
    :raises elasticsearch.exceptions.ConnectionError: If no connection could be
        established to Elasticsearch.
    """
    search = Search(using=es, index=index)

    if query:
        search = search.query(query)

    if filter_ids is not None:
        search = search.filter("ids", values=filter_ids)

    search = (
        search.sort(*as_list(sort))
        .extra(track_total_hits=True)
        .source(False)[start:end]
    )

    try:
        response = search.execute()
    except ESRequestError:
        # Ignore malformed requests.
        return None
    except ESConnectionError as e:
        if not current_app.config["ELASTICSEARCH_ENABLE_FALLBACK"]:
            current_app.logger.exception(e)

        raise
    except Exception as e:
        current_app.logger.exception(e)
        return None

    return response
