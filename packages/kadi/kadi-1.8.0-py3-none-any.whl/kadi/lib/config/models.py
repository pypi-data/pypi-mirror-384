# Copyright 2021 Karlsruhe Institute of Technology
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError

from kadi.ext.db import db
from kadi.lib.db import NestedTransaction
from kadi.lib.db import SimpleTimestampMixin
from kadi.lib.db import unique_constraint
from kadi.lib.utils import SimpleReprMixin


class ConfigItem(SimpleReprMixin, SimpleTimestampMixin, db.Model):
    """Model to store global or user-specific config items."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "key", "user_id"]
        """See :class:`.SimpleReprMixin`."""

    __tablename__ = "config_item"

    __table_args__ = (unique_constraint(__tablename__, "key", "user_id"),)

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the config item, auto incremented."""

    key = db.Column(db.Text, nullable=False)
    """The key of the config item."""

    value = db.Column(JSONB, nullable=True)
    """The value of the config item."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    """The optional ID of the :class:`.User` the config item belongs to.

    If not set, the config item is global.
    """

    user = db.relationship("User", back_populates="config_items")

    @classmethod
    def create(cls, *, key, value, user=None):
        """Create a new config item and add it to the database session.

        :param key: The key of the config item.
        :param value: The value of the config item, which needs to be JSON serializable.
        :param user: (optional) The user the config item belongs to.
        :return: The new :class:`ConfigItem` object.
        """
        config_item = cls(key=key, value=value, user=user)
        db.session.add(config_item)

        return config_item

    @classmethod
    def update_or_create(cls, *, key, value, user=None):
        """Update an existing config item or create one if it does not exist yet.

        See :meth:`create` for an explanation of the parameters.

        :return: The new or updated :class:`.ConfigItem` object.
        """
        config_item_query = cls.query.filter_by(key=key)

        if user is not None:
            config_item_query = config_item_query.filter_by(user_id=user.id)

        config_item = config_item_query.first()

        if not config_item:
            with NestedTransaction(exc=IntegrityError) as t:
                config_item = cls.create(key=key, value=value, user=user)

            if not t.success:
                config_item = config_item_query.first()

        config_item.value = value

        return config_item
