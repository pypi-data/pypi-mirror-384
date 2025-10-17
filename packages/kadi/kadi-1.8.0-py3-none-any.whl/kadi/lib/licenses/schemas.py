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
from marshmallow import ValidationError
from marshmallow import fields
from marshmallow import validates

from kadi.lib.conversion import strip
from kadi.lib.licenses.models import License
from kadi.lib.schemas import BaseSchema
from kadi.lib.schemas import CustomString


class LicenseSchema(BaseSchema):
    """Schema to represent licenses.

    See :class:`.License`.
    """

    name = CustomString(required=True, filter=strip)

    title = fields.String(dump_only=True)

    url = fields.String(dump_only=True)

    @validates("name")
    def _validate_name(self, value):
        if License.query.filter_by(name=value).first() is None:
            raise ValidationError("No license with this name exists.")
