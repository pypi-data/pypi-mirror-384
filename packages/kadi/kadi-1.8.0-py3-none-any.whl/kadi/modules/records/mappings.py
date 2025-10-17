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
from copy import deepcopy

from elasticsearch.dsl import Boolean
from elasticsearch.dsl import Date
from elasticsearch.dsl import Double
from elasticsearch.dsl import InnerDoc
from elasticsearch.dsl import Keyword
from elasticsearch.dsl import Long
from elasticsearch.dsl import Nested
from elasticsearch.dsl import Text

from kadi.lib.resources.mappings import ResourceMapping
from kadi.lib.search.core import TRIGRAM_ANALYZER

from .extras import is_nested_type


class BaseExtraMapping(InnerDoc):
    """Base search mapping for extra metadata entries of records."""

    key = Text(required=True, analyzer=TRIGRAM_ANALYZER, fields={"keyword": Keyword()})


class ExtraMappingString(BaseExtraMapping):
    """Search mapping for extra string values."""

    value = Text(analyzer=TRIGRAM_ANALYZER, fields={"keyword": Keyword()})


class ExtraMappingInteger(BaseExtraMapping):
    """Search mapping for extra integer values.

    Uses long values for the internal representation.
    """

    value = Long()

    unit = Text()


class ExtraMappingFloat(BaseExtraMapping):
    """Search mapping for extra float values.

    Uses double values for the internal representation.
    """

    value = Double()

    unit = Text()


class ExtraMappingBoolean(BaseExtraMapping):
    """Search mapping for extra boolean values."""

    value = Boolean()


class ExtraMappingDate(BaseExtraMapping):
    """Search mapping for extra date values."""

    value = Date(default_timezone="UTC")


class RecordMapping(ResourceMapping):
    """Search mapping for records.

    See :class:`.Record`.
    """

    extras_str = Nested(ExtraMappingString)

    extras_int = Nested(ExtraMappingInteger)

    extras_float = Nested(ExtraMappingFloat)

    extras_bool = Nested(ExtraMappingBoolean)

    extras_date = Nested(ExtraMappingDate)

    @classmethod
    def _flatten_extras(cls, extras, key_prefix=""):
        flat_extras = []

        for index, extra in enumerate(extras):
            if is_nested_type(extra["type"]):
                flat_extras += cls._flatten_extras(
                    extra["value"],
                    key_prefix=f"{key_prefix}{extra.get('key', index + 1)}.",
                )
            else:
                new_extra = deepcopy(extra)

                if "key" in extra:
                    new_extra["key"] = f"{key_prefix}{extra['key']}"
                else:
                    new_extra["key"] = f"{key_prefix}{index + 1}"

                flat_extras.append(new_extra)

        return flat_extras

    @classmethod
    def create_document(cls, obj):
        document = super().create_document(obj)

        type_container = {
            "extras_str": [],
            "extras_int": [],
            "extras_float": [],
            "extras_bool": [],
            "extras_date": [],
        }

        for extra in cls._flatten_extras(obj.extras):
            new_extra = {"key": extra["key"], "value": extra["value"]}

            if "unit" in extra:
                new_extra["unit"] = extra["unit"]

            type_container[f"extras_{extra['type']}"].append(new_extra)

        for type_name, extras in type_container.items():
            setattr(document, type_name, extras)

        return document
