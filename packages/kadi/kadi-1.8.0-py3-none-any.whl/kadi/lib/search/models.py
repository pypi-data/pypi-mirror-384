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
from urllib.parse import parse_qs

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import SimpleTimestampMixin
from kadi.lib.db import composite_index
from kadi.lib.db import generate_check_constraints
from kadi.lib.utils import SimpleReprMixin
from kadi.lib.utils import get_class_by_name

from .core import add_to_index
from .core import remove_from_index
from .core import search_index


class SearchableMixin:
    """Mixin for SQLALchemy models to add support for searching.

    The columns to index have to be specified in a mapping class, which has to be
    configured with its fully qualified name using ``Meta.search_mapping``.

    **Example:**

    .. code-block:: python3

        class Foo:
            class Meta:
                search_mapping = "kadi.modules.record.mapping.RecordMapping"

    After calling :meth:`register_search_listeners`, the search index will automatically
    get updated whenever an object is created or deleted or if any of the indexed
    columns (or the ``state`` column, if present) are updated using :func:`add_to_index`
    and :func:`remove_from_index`.
    """

    @classmethod
    def get_mapping_class(cls):
        """Convenience method to get the mapping class of a model."""
        return get_class_by_name(cls.Meta.search_mapping)

    @classmethod
    def search(cls, query=None, sort="_score", filter_ids=None, start=0, end=10):
        """Query the search index corresponding to this model.

        Uses :func:`search_index`, but returns the actual results instead of the raw
        search response.

        :param query: (optional) See :func:`search_index`.
        :param sort: (optional) See :func:`search_index`.
        :param filter_ids: (optional) See :func:`search_index`.
        :param start: (optional) See :func:`search_index`.
        :param end: (optional) See :func:`search_index`.
        :return: A tuple containing a list of the search results and the total amount of
            hits.
        :raises elasticsearch.exceptions.ConnectionError: If no connection could be
            established to Elasticsearch.
        """
        response = search_index(
            cls.__tablename__,
            query=query,
            sort=sort,
            filter_ids=filter_ids,
            start=start,
            end=end,
        )

        if response is None or not response.hits:
            return [], 0

        ids = [int(hit.meta.id) for hit in response.hits]
        whens = []

        for index, id in enumerate(ids):
            whens.append((id, index))

        results = (
            cls.query.filter(cls.id.in_(ids))
            .order_by(db.case(*whens, value=cls.id))
            .all()
        )

        return results, response.hits.total.value

    @classmethod
    def _before_flush_search(cls, session, flush_context, instances):
        if not hasattr(session, "_changes"):
            session._changes = {"add": set(), "remove": set()}

        for obj in session.new:
            if isinstance(obj, cls):
                session._changes["add"].add(obj)

        for obj in session.deleted:
            if isinstance(obj, cls):
                session._changes["remove"].add(obj)

        for obj in session.dirty:
            if isinstance(obj, cls) and session.is_modified(obj):
                if (
                    getattr(obj, "state", const.MODEL_STATE_ACTIVE)
                    == const.MODEL_STATE_ACTIVE
                ):
                    session._changes["add"].add(obj)
                    session._changes["remove"].discard(obj)
                else:
                    session._changes["remove"].add(obj)
                    session._changes["add"].discard(obj)

    @classmethod
    def _after_commit_search(cls, session):
        if hasattr(session, "_changes"):
            for obj in session._changes["add"]:
                add_to_index(obj)

            for obj in session._changes["remove"]:
                remove_from_index(obj)

            del session._changes

    @classmethod
    def _after_rollback_search(cls, session):
        if hasattr(session, "_changes"):
            del session._changes

    @classmethod
    def register_search_listeners(cls):
        """Register listeners to automatically update the search index.

        Uses SQLAlchemy's ``before_flush``, ``after_commit`` and ``after_rollback``
        events and propagates to all inheriting models.
        """
        db.event.listen(
            db.session, "before_flush", cls._before_flush_search, propagate=True
        )
        db.event.listen(
            db.session, "after_commit", cls._after_commit_search, propagate=True
        )
        db.event.listen(
            db.session, "after_rollback", cls._after_rollback_search, propagate=True
        )


class SavedSearch(SimpleReprMixin, SimpleTimestampMixin, db.Model):
    """Model representing saved searches."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "name", "object"]
        """See :class:`.SimpleReprMixin`."""

        check_constraints = {
            "name": {"length": {"max": 150}},
            "query_string": {"length": {"max": 4096}},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "saved_search"

    __table_args__ = (
        *generate_check_constraints(Meta.check_constraints),
        composite_index(__tablename__, "user_id", "object"),
    )

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the saved search, auto incremented."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` the saved search belongs to."""

    name = db.Column(db.Text, nullable=False)
    """The name of the saved search.

    Restricted to a maximum length of ``150`` characters.
    """

    object = db.Column(db.Text, nullable=False)
    """The type of object the saved search refers to.

    Currently always refers to a specific searchable model via its table name.
    """

    query_string = db.Column(db.Text, nullable=False)
    """The query string representing the saved search.

    This simply corresponds to the raw URL query parameter string used when searching
    the corresponding object. May be stored with or without a leading question mark.

    Restricted to a maximum length of ``4096`` characters.
    """

    user = db.relationship("User", back_populates="saved_searches")

    @property
    def qparams(self):
        """Get a dictionary representation of the query string of this saved search.

        Corresponds to the results of Python's ``urllib.parse.parse_qs``.
        """
        query_string = self.query_string

        if self.query_string.startswith("?"):
            query_string = query_string[:1]

        return parse_qs(query_string)

    @classmethod
    def create(cls, *, user, name, object, query_string):
        """Create a new saved search and add it to the database session.

        :param user: The user the saved search belongs to.
        :param name: The name of the saved search.
        :param object: The object the saved search refers to.
        :param query_string: The query string of the saved search.
        :return: The new :class:`SavedSearch` object.
        """
        saved_search = cls(
            user=user, name=name, object=object, query_string=query_string
        )
        db.session.add(saved_search)

        return saved_search
