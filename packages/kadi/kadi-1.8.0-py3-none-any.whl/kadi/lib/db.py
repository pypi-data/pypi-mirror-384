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
from datetime import timezone

import alembic
from flask import current_app
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.properties import RelationshipProperty
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.schema import Index
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.exceptions import KadiDecryptionKeyError
from kadi.lib.utils import rgetattr
from kadi.lib.utils import suppress_stderr
from kadi.lib.utils import utcnow


class KadiAesEngine(AesEngine):
    """Custom AES engine for encrypting and decrypting database values."""

    @staticmethod
    def get_secret_key():
        """Get the secret key to use for encryption.

        Note that this secret key is the same ``SECRET_KEY`` Flask uses as well, as
        specified in the application's configuration. If it ever changes, all values
        encrypted with this key will become unreadable.

        :return: The secret key.
        """
        return current_app.secret_key

    @classmethod
    def create(cls):
        """Create a new AES engine with default configuration.

        Convenience method to use the AES engine outside of an ORM context.

        :return: The created AES engine.
        """
        engine = cls()

        engine._update_key(cls.get_secret_key())
        engine._set_padding_mechanism()

        return engine

    def decrypt(self, value):
        """Try to decrypt the given value.

        :param value: The value to decrypt.
        :return: The decrypted value.
        :raises KadiDecryptionKeyError: If the key used for decrypting the value is
            invalid.
        """
        try:
            return super().decrypt(value)
        except ValueError as e:
            raise KadiDecryptionKeyError from e


class UTCDateTime(db.TypeDecorator):
    """Custom timezone aware DateTime type using UTC.

    As dates are currently saved without timezone information (and always interpreted as
    UTC), the timezone information has to be removed from datetime objects before
    persisting, as otherwise they are converted to local time. When retrieving the
    value, the timezone will be added back in.
    """

    impl = db.DateTime

    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert to UTC and then remove the timezone."""
        if value is None:
            return value

        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        """Replace the missing timezone with UTC."""
        if value is None:
            return value

        return value.replace(tzinfo=timezone.utc)


class BaseTimestampMixin:
    """Base mixin class for SQLAlchemy models to add timestamp columns.

    In all current implementations, changes in columns and relationship-based
    collections can be ignored by specifying the ``Meta.timestamp_exclude`` attribute in
    the inheriting class. It should be a list of strings specifying the attribute names
    to exclude.

    **Example:**

    .. code-block:: python3

        class Foo:
            class Meta:
                timestamp_exclude = ["bar", "baz"]
    """

    created_at = db.Column(UTCDateTime, default=utcnow, nullable=False)
    """The date and time an object has been created at.

    Always uses the current UTC time.
    """

    last_modified = db.Column(UTCDateTime, default=utcnow, nullable=False)
    """The date and time an object was last modified.

    Always uses the current UTC time as initial value. After calling
    :meth:`register_timestamp_listener` for an inheriting mixin class, this timestamp
    can automatically get updated by implementing :meth:`_before_flush_timestamp` as a
    class method.
    """

    @classmethod
    def register_timestamp_listener(cls):
        """Register a listener to automatically update the last modification timestamp.

        Uses SQLAlchemy's ``before_flush`` event and propagates to all inheriting
        models.
        """
        db.event.listen(
            db.session, "before_flush", cls._before_flush_timestamp, propagate=True
        )

    @classmethod
    def _before_flush_timestamp(cls, session, flush_context, instances):
        raise NotImplementedError

    def update_timestamp(self):
        """Manually trigger an update to the last modification timestamp."""
        self.last_modified = utcnow()


class SimpleTimestampMixin(BaseTimestampMixin):
    """Timestamp mixin class which triggers on all changes."""

    @classmethod
    def _before_flush_timestamp(cls, session, flush_context, instances):
        for obj in session.dirty:
            if isinstance(obj, cls) and session.is_modified(obj):
                excluded_attrs = rgetattr(obj.__class__, "Meta.timestamp_exclude", [])

                for attr in db.inspect(obj).attrs:
                    if attr.key in excluded_attrs or attr.key == "last_modified":
                        continue

                    if attr.load_history().has_changes():
                        obj.last_modified = utcnow()
                        break


class StateTimestampMixin(BaseTimestampMixin):
    """Timestamp mixin class which only triggers on changes in active objects.

    An object is considered active if its marked as active via its ``state`` attribute,
    which needs to be present in an inheriting model. Besides the object itself, changes
    in relationship-based collections consisting of inactive objects only are also
    ignored.
    """

    @classmethod
    def _before_flush_timestamp(cls, session, flush_context, instances):
        for obj in session.dirty:
            if isinstance(obj, cls) and session.is_modified(obj):
                # Do not update the timestamp if the state of the object (if present) is
                # not active, except for when it just changed.
                if obj.state != const.MODEL_STATE_ACTIVE:
                    history = db.inspect(obj).attrs.state.load_history()

                    if (
                        not history.deleted
                        or history.deleted[0] != const.MODEL_STATE_ACTIVE
                    ):
                        continue

                excluded_attrs = rgetattr(obj.__class__, "Meta.timestamp_exclude", [])
                timestamp_updated = False

                for attr in db.inspect(obj).attrs:
                    if timestamp_updated:
                        break

                    if attr.key in excluded_attrs or attr.key == "last_modified":
                        continue

                    history = attr.load_history()
                    items = list(history.added) + list(history.deleted)

                    for item in items:
                        # Do not update the timestamp if only changes in
                        # relationship-based collections occured and none of the related
                        # objects' state, if present, is active.
                        if (
                            not isinstance(item, db.Model)
                            or getattr(item, "state", const.MODEL_STATE_ACTIVE)
                            == const.MODEL_STATE_ACTIVE
                        ):
                            obj.last_modified = utcnow()
                            timestamp_updated = True
                            break

    def update_timestamp(self):
        """Manually trigger an update to the last modification timestamp.

        Only actually triggers the update if the object is marked as active.
        """
        if self.state == const.MODEL_STATE_ACTIVE:
            self.last_modified = utcnow()


class NestedTransaction:
    """Context manager to start a "nested" transaction.

    The nested transaction uses the ``SAVEPOINT`` feature of the database, which will be
    triggered when entering the context manager. Once the context manager exits, the
    savepoint is released, which does not actually persist the changes done in the
    savepoint yet. If the release produces the given exception, the savepoint will be
    rolled back automatically. The ``success`` attribute of the transaction can be used
    to check the result of the release operation afterwards.

    :param exc: (optional) The exception to catch when releasing the savepoint.
    """

    def __init__(self, exc=SQLAlchemyError):
        self.exc = exc
        self._success = False
        self._savepoint = None

    def __enter__(self):
        self._savepoint = db.session.begin_nested()
        return self

    def __exit__(self, type, value, traceback):
        try:
            self._savepoint.commit()
            self._success = True
        except self.exc:
            self._savepoint.rollback()

    @property
    def success(self):
        """Get the status of the nested transaction once the savepoint is released.

        Will always be ``False`` before the context manager exits.
        """
        return self._success


def update_object(obj, **kwargs):
    r"""Convenience function to update database objects.

    Only columns (i.e. attributes) that actually exist will get updated.

    :param obj: The object to update.
    :param \**kwargs: The columns to update and their respective values.
    """
    for key, value in kwargs.items():
        if hasattr(obj, key):
            setattr(obj, key, value)


def composite_index(tablename, *cols):
    r"""Generate a composite index.

    :param tablename: The name of the table.
    :param \*cols: The names of the columns.
    :return: The Index instance.
    """
    return Index(f"ix_{tablename}_{'_'.join(cols)}", *cols)


def unique_constraint(tablename, *cols):
    r"""Generate a unique constraint.

    :param tablename: The name of the table.
    :param \*cols: The names of the columns.
    :return: The UniqueConstraint instance.
    """
    return UniqueConstraint(*cols, name=f"uq_{tablename}_{'_'.join(cols)}")


def check_constraint(constraint, name):
    """Generate a check constraint.

    :param constraint: The constraint expression as string.
    :param name: The name of the constraint.
    :return: The CheckConstraint instance.
    """
    return CheckConstraint(constraint, name=f"ck_{name}")


def length_constraint(col, min_value=None, max_value=None):
    """Generate a length check constraint for a column.

    :param col: The name of the column.
    :param min_value: (optional) Minimum length.
    :param max_value: (optional) Maximum length.
    :return: The CheckConstraint instance.
    """
    constraint = ""
    if min_value is not None:
        constraint += f"char_length({col}) >= {min_value}"

    if max_value is not None:
        if min_value is not None:
            constraint += " AND "

        constraint += f"char_length({col}) <= {max_value}"

    return check_constraint(constraint, name=f"{col}_length")


def range_constraint(col, min_value=None, max_value=None):
    """Generate a range check constraint for a column.

    :param col: The name of the column.
    :param min_value: (optional) Minimum value.
    :param max_value: (optional) Maximum value.
    :return: The CheckConstraint instance.
    """
    constraint = ""

    if min_value is not None:
        constraint += f"{col} >= {min_value}"

    if max_value is not None:
        if min_value is not None:
            constraint += " AND "

        constraint += f"{col} <= {max_value}"

    return check_constraint(constraint, name=f"{col}_range")


def values_constraint(col, values):
    """Generate a values check constraint for a column.

    :param col: The name of the column.
    :param values: List of values.
    :return: The CheckConstraint instance.
    """
    values = values if values is not None else []
    values = ", ".join(f"'{value}'" for value in values)

    constraint = f"{col} IN ({values})"
    return check_constraint(constraint, name=f"{col}_values")


def generate_check_constraints(constraints):
    """Generate database check constraints.

    Supports check constraints of type ``"length"``, ``"range"`` and ``"values"``. The
    constraints have to be given in the following form:

    .. code-block:: python3

        {
            "col_1": {"length": {"min": 0, "max": 10}},
            "col_2": {"range": {"min": 0, "max": 10}},
            "col_3": {"values": ["val_1", "val_2"]},
        }

    :param constraints: Dictionary of constraints to generate.
    :return: A tuple of CheckConstraint instances.
    """
    results = []

    for col, constraint in constraints.items():
        for name, args in constraint.items():
            if name == "length":
                results.append(
                    length_constraint(
                        col, min_value=args.get("min"), max_value=args.get("max")
                    )
                )
            elif name == "range":
                results.append(
                    range_constraint(
                        col, min_value=args.get("min"), max_value=args.get("max")
                    )
                )
            elif name == "values":
                results.append(values_constraint(col, args))

    return tuple(results)


def get_class_by_tablename(tablename):
    """Get the model class mapped to a certain database table name.

    :param tablename: Name of the table.
    :return: The class reference or ``None`` if the table does not exist.
    """
    for mapper in db.Model.registry.mappers:
        if getattr(mapper.class_, "__tablename__", None) == tablename:
            return mapper.class_

    return None


def is_column(model, attr):
    """Check if a model's attribute is a regular column.

    :param model: The model that contains the column.
    :param attr: Name of the column attribute.
    :return: ``True`` if the attribute is a column, ``False`` otherwise.
    """
    return isinstance(getattr(model, attr).property, ColumnProperty)


def get_column_type(model, attr):
    """Get the type of a column.

    :param model: The model that contains the column.
    :param attr: Name of the column attribute.
    :return: The type of the column or ``None`` if the attribute is not a regular
        column.
    """
    if is_column(model, attr):
        return getattr(model, attr).property.columns[0].type

    return None


def is_relationship(model, attr):
    """Check if a model's attribute is a relationship.

    :param model: The model that contains the column.
    :param attr: Name of the relationship attribute.
    :return: ``True`` if the attribute is a relationship, ``False`` otherwise.
    """
    return isinstance(getattr(model, attr).property, RelationshipProperty)


def is_many_relationship(model, attr):
    """Check if a model's attribute is a many-relationship.

    :param model: The model that contains the column.
    :param attr: Name of the relationship attribute.
    :return: ``True`` if the attribute is a many-relationship, ``False`` otherwise.
    """
    if is_relationship(model, attr):
        return getattr(model, attr).property.uselist

    return False


def get_class_of_relationship(model, attr):
    """Get the class of a relationship.

    :param model: The model that contains the relationship.
    :param attr: Name of the relationship attribute.
    :return: The class reference  or ``None`` if the attribute is not a relationship.
    """
    if is_relationship(model, attr):
        return getattr(model, attr).property.mapper.class_

    return None


def escape_like(value, escape="\\"):
    """Escape a string for use in LIKE queries.

    Will escape ``"%"``, ``"_"`` and the escape character specified by ``escape``.

    :param value: The string to escape.
    :param escape: (optional) The escape character to use.
    :return: The escaped string.
    """
    return (
        value.replace(escape, 2 * escape)
        .replace("%", f"{escape}%")
        .replace("_", f"{escape}_")
    )


def acquire_lock(obj):
    """Acquire a database lock on a given object.

    The database row corresponding to the given object will be locked using ``FOR
    UPDATE`` until the session is committed or rolled back. Once the lock is acquired,
    the given object is also refreshed. Should only be used if strictly necessary, e.g.
    to prevent certain race conditions.

    :param obj: The object to lock.
    :return: The locked and refreshed object.
    """
    return (
        obj.__class__.query.populate_existing()
        .with_for_update()
        .filter(obj.__class__.id == obj.id)
        .first()
    )


def has_extension(extension_name):
    """Check if a given database extension is installed.

    :param extension_name: The name of the extension.
    :return: ``True`` if the extension is installed, ``False`` otherwise.
    """
    return (
        db.session.execute(
            db.text("SELECT * FROM pg_extension WHERE extname=:extname"),
            {"extname": extension_name},
        ).first()
        is not None
    )


def get_disk_space():
    """Get the used disk space of the database.

    :return: The disk space of the database in bytes.
    """
    return (
        db.session.execute(
            db.text(f"SELECT pg_database_size('{db.engine.url.database}')"),
        ).scalar()
        or 0
    )


def has_pending_revisions():
    """Check if the database has pending revisions.

    :return: ``True`` if there are pending revisions, ``False`` otherwise.
    """
    migration_config = current_app.extensions["migrate"].migrate.get_config()
    script_dir = alembic.script.ScriptDirectory.from_config(migration_config)
    latest_revision = script_dir.get_current_head()

    with suppress_stderr():
        with db.engine.connect() as connection:
            migration_context = alembic.runtime.migration.MigrationContext.configure(
                connection
            )
            current_revision = migration_context.get_current_revision()

    return current_revision != latest_revision
