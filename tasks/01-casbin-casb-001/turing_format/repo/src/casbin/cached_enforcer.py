# Copyright 2021 The casbin Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from casbin.enforcer import Enforcer


class CachedEnforcer(Enforcer):
    """CachedEnforcer wraps Enforcer with an in-memory decision cache.

    In hot authorization paths the same request tuple ``(sub, obj, act)`` is
    evaluated over and over. ``CachedEnforcer`` remembers the boolean result of
    a request so that repeated identical calls can return without re-running the
    matcher.

    The intended surface is:

    * ``enforce(*rvals)`` returns the same boolean as ``Enforcer.enforce`` but
      serves repeated identical requests from the cache.
    * ``enable_cache(enabled)`` turns caching on or off. When caching is off the
      enforcer behaves exactly like the base ``Enforcer``.
    * ``get_cache_stats()`` returns a small JSON-serializable dict describing
      whether the cache is enabled, how many hits and misses have occurred, and
      the current number of cached entries.

    The cache is enabled by default. A runtime permission edit made through the
    management API must be reflected by the next ``enforce`` call, and it should
    keep the rest of the cache warm rather than discarding unrelated decisions.
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("CachedEnforcer is not implemented yet")
