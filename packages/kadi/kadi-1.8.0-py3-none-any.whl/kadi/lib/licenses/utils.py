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
from .core import get_builtin_licenses
from .models import License


def initialize_builtin_licenses():
    """Initialize all built-in licenses in the database.

    Will create database objects of the licenses returned by
    :func:`get_builtin_licenses`.

    :return: ``True`` if at least one license was created, ``False`` otherwise.
    """
    license_created = False

    for name, license_meta in get_builtin_licenses().items():
        if License.query.filter_by(name=name).first() is None:
            License.create(
                name=name, title=license_meta["title"], url=license_meta["url"]
            )
            license_created = True

    return license_created
