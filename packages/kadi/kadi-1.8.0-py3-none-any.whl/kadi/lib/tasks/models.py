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
from uuid import uuid4

from flask_babel import gettext as _
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID

from kadi.ext.db import db
from kadi.lib.db import SimpleTimestampMixin
from kadi.lib.db import composite_index
from kadi.lib.db import generate_check_constraints
from kadi.lib.utils import SimpleReprMixin
from kadi.lib.utils import StringEnum


class TaskState(StringEnum):
    """String enum containing all possible state values for tasks.

    * ``PENDING``: For tasks that have been queued.
    * ``RUNNING``: For tasks that are currently running.
    * ``REVOKED``: For tasks that have been revoked.
    * ``SUCCESS``: For tasks that finished successfuly.
    * ``FAILURE``: For tasks that finished with an error.
    """

    __values__ = ["pending", "running", "revoked", "success", "failure"]


class Task(SimpleReprMixin, SimpleTimestampMixin, db.Model):
    """Model to represent tasks."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "name", "state"]
        """See :class:`.SimpleReprMixin`."""

        check_constraints = {
            "progress": {"range": {"min": 0, "max": 100}},
            "state": {"values": TaskState.__values__},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "task"

    __table_args__ = (
        *generate_check_constraints(Meta.check_constraints),
        composite_index(__tablename__, "user_id", "name", "state"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    """The ID of the task, auto incremented."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    """The optional ID of the :class:`.User` who started the task."""

    name = db.Column(db.Text, nullable=False)
    """The name of the task."""

    arguments = db.Column(JSONB, nullable=False)
    """The arguments of the task.

    Stored in the following form as JSON:

    .. code-block:: json

        {
            "args": ["foo"],
            "kwargs": {
                "bar": "baz"
            }
        }
    """

    progress = db.Column(db.Integer, default=0, nullable=False)
    """The progress of the task.

    Must be a value between ``0`` and ``100``.
    """

    result = db.Column(JSONB, nullable=True)
    """The optional result of the task, depending on the type of task."""

    state = db.Column(db.Text, index=True, nullable=False)
    """The state of the task.

    See :class:`.TaskState`.
    """

    creator = db.relationship("User", back_populates="tasks")

    @property
    def is_revoked(self):
        """Check if a task is revoked.

        Will always refresh the task object to get up to date values, as revoking
        usually happens outside the current database session context (e.g. in another
        process).
        """
        db.session.refresh(self)
        return self.state == TaskState.REVOKED

    @property
    def pretty_state(self):
        """Get the state of a task in a human-readable and translated format."""
        if self.state == TaskState.PENDING:
            return _("Pending")
        if self.state == TaskState.RUNNING:
            return _("Running")
        if self.state == TaskState.SUCCESS:
            return _("Success")
        if self.state == TaskState.FAILURE:
            return _("Failure")
        if self.state == TaskState.REVOKED:
            return _("Revoked")

        return _("Unknown")

    @classmethod
    def create(cls, *, creator, name, args=None, kwargs=None, state=TaskState.PENDING):
        """Create a new task and add it to the database session.

        :param creator: The user who is starting the task.
        :param name: The name of the task.
        :param args: (optional) The positional arguments of the task as list.
        :param kwargs: (optional) The keyword arguments of the task as dictionary.
        :param state: (optional) The state of the task.
        :return: The new :class:`Task` object.
        """
        arguments = {
            "args": args if args is not None else [],
            "kwargs": kwargs if kwargs is not None else {},
        }

        task = cls(creator=creator, name=name, arguments=arguments, state=state)
        db.session.add(task)

        return task

    def revoke(self):
        """Revoke a task if it is still pending or running."""
        if self.state in {TaskState.PENDING, TaskState.RUNNING}:
            self.state = TaskState.REVOKED

    def update_progress(self, percent):
        """Update a tasks progress.

        :param percent: The progress in percent, which needs to be an integer or float
            value between ``0`` and ``100``.
        """
        if 0 <= percent <= 100:
            self.progress = int(percent)
