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
from sqlalchemy import null
from sqlalchemy.dialects.postgresql import JSONB

from kadi.ext.db import db
from kadi.lib.db import acquire_lock
from kadi.lib.db import get_class_by_tablename
from kadi.lib.db import get_column_type
from kadi.lib.db import is_many_relationship
from kadi.lib.utils import SimpleReprMixin
from kadi.lib.utils import rgetattr

from .models import Revision
from .utils import get_revision_columns


def _get_relationship_values(obj, relationship, attrs):
    relationship_obj = getattr(obj, relationship)

    # For many-relationships, get a list of dictionaries of all revisioned relationship
    # columns.
    if is_many_relationship(obj.__class__, relationship):
        values = []

        # Always order by ID to get deterministic results.
        for relationship_obj in relationship_obj.order_by("id"):
            values_dict = {}

            for attr in attrs:
                values_dict[attr] = getattr(relationship_obj, attr)

            values.append(values_dict)

    # Otherwise, get only a single dictionary of all revisioned relationship columns or
    # None in case the object is None as well.
    else:
        if relationship_obj is not None:
            values = {}

            for attr in attrs:
                values[attr] = getattr(relationship_obj, attr)
        else:
            return None

    return values


def _has_changes(obj, parent_revision, columns, relationships):
    if parent_revision is None:
        return True

    for column in columns:
        if getattr(obj, column) != getattr(parent_revision, column):
            return True

    for relationship, attrs in relationships:
        values = _get_relationship_values(obj, relationship, attrs)

        if values != getattr(parent_revision, relationship):
            return True

    return False


def create_revision(obj, user=None):
    """Create a new revision of an object.

    If none of the revisioned values changed, no new revision will be created. See also
    :func:`kadi.lib.revisions.core.setup_revisions`.

    Note that this function acquires a lock on the given object.

    :param obj: The object to create a new revision for.
    :param user: (optional) The user who triggered the revision.
    :return: The created object revision or ``None`` if no new revision was created.
    """

    # Ensure that all current changes are flushed to the database.
    db.session.flush()

    # Acquire a lock on the given object to ensure that the parent revision is always
    # the latest one.
    obj = acquire_lock(obj)

    columns, relationships = get_revision_columns(obj.__class__)
    parent_revision = obj.ordered_revisions.first()

    # Check if any of the revisioned values changed.
    if not _has_changes(obj, parent_revision, columns, relationships):
        return None

    obj_revision = obj.revision_class()
    db.session.add(obj_revision)

    obj_revision.revision = Revision.create(user=user)
    obj_revision.parent = parent_revision
    setattr(obj_revision, obj.__tablename__, obj)

    for column in columns:
        setattr(obj_revision, column, getattr(obj, column))

    for relationship, attrs in relationships:
        values = _get_relationship_values(obj, relationship, attrs)

        # The normal None value will be represented as a JSON null value otherwise.
        if values is None:
            values = null()

        setattr(obj_revision, relationship, values)

    return obj_revision


def delete_revisions(obj):
    """Delete all revisions of an object.

    :param obj: The object to delete the revisions of.
    """

    # Delete the object revisions first.
    base_revision_ids = []

    for obj_revision in obj.revisions:
        base_revision_ids.append(obj_revision.revision_id)
        db.session.delete(obj_revision)

    # And then the corresponding base revision objects.
    for revision in Revision.query.filter(Revision.id.in_(base_revision_ids)):
        db.session.delete(revision)


def _make_revision_model(model, classname, tablename):
    columns, relationships = get_revision_columns(model)

    class_dict = {
        # Meta attributes.
        "__tablename__": tablename,
        "Meta": type(
            "Meta",
            (),
            {
                "representation": (
                    [
                        "id",
                        "revision_id",
                        f"{model.__tablename__}_id",
                        f"{tablename}_id",
                    ]
                )
            },
        ),
        # ID of the object revision itself.
        "id": db.Column(db.Integer, primary_key=True),
        # ID of the base revision.
        "revision_id": db.Column(
            db.Integer, db.ForeignKey("revision.id"), nullable=False
        ),
        # Relationship of the base revision.
        "revision": db.relationship("Revision"),
        # ID of the revisioned object.
        f"{model.__tablename__}_id": db.Column(
            get_column_type(model, "id"),
            db.ForeignKey(f"{model.__tablename__}.id"),
            nullable=False,
        ),
        # Relationship of the revisioned object.
        model.__tablename__: db.relationship(
            model.__name__, backref=db.backref("revisions", lazy="dynamic")
        ),
        # ID of the parent object revision.
        f"{tablename}_id": db.Column(
            db.Integer, db.ForeignKey(f"{tablename}.id"), nullable=True
        ),
        # Relationship of the parent object revision.
        "parent": db.relationship(
            classname,
            remote_side=f"{classname}.id",
            backref=db.backref("child", uselist=False),
        ),
        # Reference to the class of the revisioned model.
        "model_class": model,
        # Convenience property for the revisioned object, independent of tablename.
        "object": property(lambda self: getattr(self, model.__tablename__)),
        # Convenience property for the user ID of the base revision.
        "user_id": property(lambda self: self.revision.user_id),
        # Convenience property for the timestamp of the base revision.
        "timestamp": property(lambda self: self.revision.timestamp),
        # Convenience property for the user of the base revision.
        "user": property(lambda self: self.revision.user),
    }

    for column in columns:
        if column not in class_dict:
            class_dict[column] = db.Column(
                get_column_type(model, column), nullable=True
            )

    for relationship, _ in relationships:
        if relationship not in class_dict:
            # We simply use JSON to store the relationship values.
            class_dict[relationship] = db.Column(JSONB, nullable=True)

    return type(classname, (SimpleReprMixin, db.Model), class_dict)


def setup_revisions():
    """Setup revisioning for all models that support it.

    The columns to store revisions of have to be specified in a ``Meta.revision``
    attribute in each model. It should be a list of strings specifying the attribute
    names.

    **Example:**

    .. code-block:: python3

        class Foo:
            class Meta:
                revision = ["bar", "baz[foo, bar]"]

    The columns can either be regular columns, like the first value in the list, or
    relationships like the second value. For the latter, all regular columns of the
    relationship that should be included in the revision need to be specified in square
    brackets, separated by commas.

    For each model, a new model class for the revisions will be created automatically,
    linked to the original model class and to :class:`.Revision`. The class of the
    revisioned model will also be stored on each new revision model as ``model_class``.
    Additionally, the revision model class will be stored on the original model as
    ``revision_class`` as well as a convenience property to retrieve the revisions in
    descending order of their timestamp as ``ordered_revisions``.
    """

    # Make a copy of the keys as we might be adding new tables while iterating.
    for tablename in list(db.metadata.tables.keys()):
        model = get_class_by_tablename(tablename)

        if rgetattr(model, "Meta.revision", None) is not None:
            revision_classname = f"{model.__name__}Revision"
            revision_tablename = f"{model.__tablename__}_revision"

            # Stops SQLAlchemy from complaining when the dev server is reloading.
            if db.metadata.tables.get(revision_tablename) is not None:
                return

            revision_model = _make_revision_model(
                model, revision_classname, revision_tablename
            )

            # Setup some convenience attributes.
            model.revision_class = revision_model
            model.ordered_revisions = property(
                lambda self: self.revisions.join(Revision).order_by(
                    Revision.timestamp.desc()
                )
            )
