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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from kadi.ext.db import db
from kadi.lib.db import NestedTransaction
from kadi.lib.db import generate_check_constraints
from kadi.lib.utils import SimpleReprMixin


class TaggingMixin:
    """Mixin for SQLALchemy models to add support for tagging.

    The model needs a many-to-many ``tags`` relationship connecting itself with the
    :class:`.Tag` model.
    """

    def set_tags(self, names):
        """Set one or more tags.

        Will create a new tag object for each tag name that does not yet exist in the
        database and add it to the relationship. Existing tags from the relationship
        that are not in the given list are removed.

        :param names: A list of tag names.
        :return: ``True`` if the tags were set successfully, ``False`` otherwise.
        """
        with NestedTransaction(exc=StaleDataError) as t:
            for tag in self.tags:
                if tag.name not in names:
                    self.tags.remove(tag)

        if not t.success:
            return False

        with NestedTransaction(exc=IntegrityError) as t:
            for name in names:
                tag = Tag.get_or_create(name)

                if tag not in self.tags:
                    self.tags.append(tag)

        return t.success


class Tag(SimpleReprMixin, db.Model):
    """Model to represent tags."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "name"]
        """See :class:`.SimpleReprMixin`."""

        check_constraints = {
            "name": {"length": {"max": 50}},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "tag"

    __table_args__ = generate_check_constraints(Meta.check_constraints)

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the tag, auto incremented."""

    name = db.Column(db.Text, index=True, unique=True, nullable=False)
    """The unique name of the tag.

    Restricted to a maximum length of ``50`` characters.
    """

    records = db.relationship(
        "Record", secondary="record_tag", lazy="dynamic", back_populates="tags"
    )

    collections = db.relationship(
        "Collection", secondary="collection_tag", lazy="dynamic", back_populates="tags"
    )

    @classmethod
    def create(cls, *, name):
        """Create a new tag and add it to the database session.

        :param name: The name of the tag.
        :return: The new :class:`Tag` object.
        """
        tag = cls(name=name)
        db.session.add(tag)

        return tag

    @classmethod
    def get_or_create(cls, name):
        """Return an existing tag or create one if it does not exist yet.

        See :meth:`create` for an explanation of the parameters.

        :return: The new or existing :class:`.Tag` object.
        """
        tag_query = cls.query.filter_by(name=name)
        tag = tag_query.first()

        if not tag:
            with NestedTransaction(exc=IntegrityError) as t:
                tag = cls.create(name=name)

            if not t.success:
                tag = tag_query.first()

        return tag
