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
from sqlalchemy.dialects.postgresql import JSONB

from kadi.ext.db import db
from kadi.lib.db import SimpleTimestampMixin
from kadi.lib.db import generate_check_constraints
from kadi.lib.utils import SimpleReprMixin


class Workflow(SimpleReprMixin, SimpleTimestampMixin, db.Model):
    """Model to represent workflows.

    Currently not used anymore, as workflows are represented as record files, but may
    still be repurposed in the future.
    """

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "user_id", "name"]
        """See :class:`.SimpleReprMixin`."""

        check_constraints = {
            "name": {"length": {"max": 150}},
        }
        """See :func:`kadi.lib.db.generate_check_constraints`."""

    __tablename__ = "workflow"

    __table_args__ = generate_check_constraints(Meta.check_constraints)

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the workflow, auto incremented."""

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    """The ID of the :class:`.User` who created the workflow."""

    name = db.Column(db.Text, nullable=False)
    """The name of the workflow.

    Restricted to a maximum length of ``150`` characters.
    """

    data = db.Column(JSONB, nullable=False)
    """The data of the workflow."""

    creator = db.relationship("User", back_populates="workflows")

    @classmethod
    def create(cls, *, creator, name, data):
        """Create a new workflow and add it to the database session.

        :param creator: The creator of the workflow.
        :param name: The name of the workflow.
        :param data: The data of the workflow.
        :return: The new :class:`Workflow` object.
        """
        workflow = cls(creator=creator, name=name, data=data)
        db.session.add(workflow)

        return workflow
