# Copyright 2024 Karlsruhe Institute of Technology
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
from elasticsearch.dsl import Date
from elasticsearch.dsl import Keyword
from elasticsearch.dsl import MetaField
from elasticsearch.dsl import Text

from kadi.lib.search.core import TRIGRAM_ANALYZER
from kadi.lib.search.core import BaseMapping


class ResourceMapping(BaseMapping):
    """Base search mapping class to represent different kinds of resources.

    These resources may refer to instances of :class:`.Record`, :class:`.Collection`,
    :class:`.Template` or :class:`.Group`.
    """

    class Meta:
        """Container to store meta class attributes."""

        dynamic = MetaField(False)

    identifier = Text(
        required=True,
        analyzer=TRIGRAM_ANALYZER,
        fields={"text": Text(), "keyword": Keyword()},
    )

    title = Text(
        required=True,
        analyzer=TRIGRAM_ANALYZER,
        fields={"text": Text(), "keyword": Keyword()},
    )

    plain_description = Text(required=True)

    created_at = Date(required=True, default_timezone="UTC")

    last_modified = Date(required=True, default_timezone="UTC")
