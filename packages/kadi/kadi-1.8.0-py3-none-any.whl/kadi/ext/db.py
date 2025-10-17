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
from flask import abort
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.model import Model
from flask_sqlalchemy.query import Query
from sqlalchemy import MetaData

import kadi.lib.constants as const


NAMING_CONVENTION = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
}


class KadiModel(Model):
    """Custom SQLAlchemy model class.

    Enables equality checking of all inheriting models by simply comparing the primary
    ``id`` column, which is assumed to exist in each model.
    """

    # Restore the default implementation.
    __hash__ = object.__hash__

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id

        return NotImplemented

    def __ne__(self, other):
        equal = self.__eq__(other)

        if equal is NotImplemented:
            return NotImplemented

        return not equal


class KadiQuery(Query):
    """Custom SQLAlchemy query class."""

    def get_active(self, ident, attr="state", value=const.MODEL_STATE_ACTIVE):
        """Convenience method to get an active item.

        In this context active means having some state attribute set to a specific
        value.

        :param ident: The primary key value of the item.
        :param attr: (optional) The name of the state attribute.
        :param value: (optional) The value the state attribute needs for the item to be
            considered active.
        :return: The active item or ``None`` if the item was not found or is inactive.
        """
        item = self.get(ident)

        if item is not None:
            state = getattr(item, attr, None)

            if state is not None and state == value:
                return item

        return None

    def get_active_or_404(self, ident, attr="state", value=const.MODEL_STATE_ACTIVE):
        """Convenience method to get an active item or abort with 404.

        Uses :meth:`get_active`, but aborts with an exception if no active item was
        found.

        :param ident: See :meth:`get_active`.
        :param attr: (optional) See :meth:`get_active`.
        :param value: (optional) See :meth:`get_active`.
        :return: The active item.
        :raises werkzeug.exceptions.NotFound: If the item was not found or is inactive.
        """
        item = self.get_active(ident)

        if item is None:
            abort(404)

        return item


metadata = MetaData(naming_convention=NAMING_CONVENTION)
db = SQLAlchemy(metadata=metadata, model_class=KadiModel, query_class=KadiQuery)
