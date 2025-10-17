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
from kadi.ext.db import db
from kadi.lib.utils import SimpleReprMixin


class License(SimpleReprMixin, db.Model):
    """Model to represent licenses."""

    class Meta:
        """Container to store meta class attributes."""

        representation = ["id", "name"]
        """See :class:`.SimpleReprMixin`."""

    __tablename__ = "license"

    id = db.Column(db.Integer, primary_key=True)
    """The ID of the license, auto incremented."""

    name = db.Column(db.Text, unique=True, nullable=False)
    """The unique name of the license."""

    title = db.Column(db.Text, nullable=False)
    """The title of the license."""

    url = db.Column(db.Text, nullable=True)
    """The optional URL of the license."""

    records = db.relationship("Record", lazy="dynamic", back_populates="license")

    @classmethod
    def create(cls, *, name, title, url=None):
        """Create a new license and add it to the database session.

        :param name: The name of the license.
        :param title: The title of the license.
        :param url: (optional) The URL of the license.
        :return: The new :class:`License` object.
        """
        license = cls(name=name, title=title, url=url)
        db.session.add(license)

        return license
