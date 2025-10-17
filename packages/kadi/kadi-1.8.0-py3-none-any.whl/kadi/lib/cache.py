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
from functools import wraps
from inspect import signature

from flask import current_app
from flask import g
from flask import has_request_context


def _make_hashable(obj):
    if isinstance(obj, (list, set)):
        return tuple(_make_hashable(item) for item in obj)

    if isinstance(obj, dict):
        return frozenset((k, _make_hashable(v)) for k, v in obj.items())

    return obj


def memoize_request(func):
    """Decorator to cache a function call's result during a request.

    Uses an in-memory dictionary as cache that will be deleted again after the current
    request. The function's fully qualified name and arguments will be used as key to
    store its result for following calls.

    Can be disabled for individual function calls by passing ``_disable_cache=True`` to
    a memoized function. Note that during testing, memoization is disabled
    automatically.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        disable_cache = kwargs.pop("_disable_cache", False)

        if not has_request_context() or disable_cache or current_app.testing:
            return func(*args, **kwargs)

        bound_args = signature(func).bind(*args, **kwargs)
        bound_args.apply_defaults()

        key = (
            func.__module__,
            func.__name__,
            _make_hashable(dict(bound_args.arguments)),
        )

        # pylint: disable=assigning-non-slot
        if not hasattr(g, "_cache"):
            g._cache = {}

        if key not in g._cache:
            g._cache[key] = func(*args, **kwargs)

        return g._cache[key]

    return wrapper
