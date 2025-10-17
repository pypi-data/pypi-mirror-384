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

from kadi.ext.db import db
from kadi.lib.db import UTCDateTime
from kadi.lib.db import unique_constraint
from kadi.lib.utils import SimpleReprMixin
from kadi.lib.utils import utcnow


class FavoriteMixin:
    """Mixin for SQLALchemy models to check whether an object is favorited."""

    def is_favorite(self, user=None):
        """Check if the current object is favorited by the given user.

        Wraps :func:`is_favorite` with the type and ID of the current object.

        :param user: (optional) The user the favorite belongs to. Defaults to the
            current user.
        :return: See :func:`is_favorite`.
        """
        from .core import is_favorite

        user = user if user is not None else current_user

        return is_favorite(self.__tablename__, self.id, user=user)


class Favorite(SimpleReprMixin, db.Model):
    """Model representing favorited objects.

    Each favorite is associated with a user, a specific type of object and an ID
    referring to a specific object instance.
    """

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "object", "object_id"]
        """See :class:`.SimpleReprMixin`."""

    __tablename__ = "favorite"

    __table_args__ = (
        unique_constraint(__tablename__, "user_id", "object", "object_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the favorite, auto incremented."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` the favorite belongs to."""

    object = db.Column(db.Text, nullable=False)
    """The type of object the favorite refers to.

    Currently always refers to a specific model via its table name.
    """

    object_id = db.Column(db.Integer, nullable=False)
    """The ID of the object the favorite refers to."""

    created_at = db.Column(UTCDateTime, default=utcnow, nullable=False)
    """The date and time the favorite was created at."""

    user = db.relationship("User", back_populates="favorites")

    @classmethod
    def create(cls, *, user, object, object_id):
        """Create a new favorite and add it to the database session.

        :param user: The user the favorite belongs to.
        :param object: The type of object the favorite refers to.
        :param object_id: The ID of the object.
        :return: The new :class:`Favorite` object.
        """
        favorite = cls(user=user, object=object, object_id=object_id)
        db.session.add(favorite)

        return favorite
