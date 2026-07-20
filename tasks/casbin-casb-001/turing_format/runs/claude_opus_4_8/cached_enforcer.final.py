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

from collections import OrderedDict

from casbin.core_enforcer import EnforceContext
from casbin.enforcer import Enforcer


# Default upper bound on the number of cached decisions. The cache behaves like
# a plain dict until it reaches this many entries, after which the
# least-recently-used decision is dropped. This keeps the memory footprint of a
# long-running process bounded even if it is fed an unbounded variety of
# requests. Pass ``cache_max_size=None`` for an unbounded cache.
DEFAULT_MAX_CACHE_SIZE = 10000

# Sentinel distinguishing "not cached" from a cached ``False`` decision.
_MISS = object()


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

    Invalidation strategy
    ---------------------
    Every policy mutation funnels through the internal ``_add_policy`` /
    ``_remove_policy`` / ``_update_*`` methods, so those are intercepted here.
    When a rule changes we only evict the cached requests that *could* be
    affected by it: a request is considered affected when it shares at least one
    token value with the changed rule (for example, editing
    ``p, alice, data1, read`` evicts a cached ``("alice", "data1", "read")`` but
    leaves an unrelated ``("bob", "data2", "write")`` warm). Anything the change
    cannot touch stays cached, so a routine permission edit keeps the hit rate
    high instead of dumping the whole cache.

    A request can only be allowed by a policy rule when their compared fields
    line up, so for the direct and single-hop RBAC models this token-overlap
    test never keeps a decision it needs to drop. (Multi-hop role-to-role edits
    -- e.g. linking two roles that share no token with the cached subject -- are
    the known limitation of a purely lexical test; for those, reload the policy
    or call :meth:`clear_cache`.)

    Wholesale changes -- reloading, clearing, or rebuilding the entire policy --
    invalidate the whole cache, which is both correct and rare.

    Note: like the upstream ``CachedEnforcer``, this class is not thread-safe.
    Use ``SyncedEnforcer`` when concurrent access is required.
    """

    def __init__(self, *args, enable_cache=True, cache_max_size=DEFAULT_MAX_CACHE_SIZE, **kwargs):
        # An OrderedDict lets us evict in least-recently-used order in O(1)
        # without pulling in a third-party cache. It behaves like a plain dict
        # keyed by the request tuple for the common (bounded) case.
        self._cache = OrderedDict()
        self._cache_enabled = bool(enable_cache)
        self._cache_max_size = cache_max_size
        self._cache_hits = 0
        self._cache_misses = 0
        super().__init__(*args, **kwargs)

    # -- public cache API ---------------------------------------------------

    def enable_cache(self, enabled=True):
        """enables or disables the decision cache.

        When disabled, ``enforce`` behaves exactly like the base ``Enforcer``:
        no lookups, no stores, no caching at all. The cached entries are dropped
        on any toggle so that re-enabling never serves a stale decision.
        """
        self._cache_enabled = bool(enabled)
        self.clear_cache()

    def get_cache_stats(self):
        """returns a small JSON-serializable snapshot of cache activity.

        Keys are plain JSON types so the dict can be scraped straight into a
        metrics pipeline:

        * ``enabled`` (bool): whether caching is currently on.
        * ``hits`` (int): number of requests served from the cache.
        * ``misses`` (int): number of requests that had to run the matcher.
        * ``size`` (int): number of decisions currently cached.
        """
        return {
            "enabled": bool(self._cache_enabled),
            "hits": int(self._cache_hits),
            "misses": int(self._cache_misses),
            "size": len(self._cache),
        }

    def clear_cache(self):
        """drops every cached decision, leaving the hit/miss counters intact."""
        self._cache.clear()

    # -- enforcement --------------------------------------------------------

    def enforce(self, *rvals):
        """decides whether a request is allowed, serving repeats from the cache.

        Returns the same boolean as ``Enforcer.enforce``. Identical requests are
        answered from the cache instead of re-running the matcher.
        """
        if not self._cache_enabled:
            return super().enforce(*rvals)

        key = self._make_key(rvals)
        if key is None:
            # The request cannot be used as a stable cache key (e.g. it carries
            # an EnforceContext or an unhashable value), so fall back to the
            # base enforcer rather than risk a wrong cache hit.
            return super().enforce(*rvals)

        cached = self._cache.get(key, _MISS)
        if cached is not _MISS:
            self._cache_hits += 1
            # Mark as most-recently-used for the LRU bound. O(1), so a cache hit
            # stays cheap on the hot path.
            self._cache.move_to_end(key)
            return cached

        self._cache_misses += 1
        result = super().enforce(*rvals)
        self._store(key, result)
        return result

    # -- key handling / storage --------------------------------------------

    @staticmethod
    def _make_key(rvals):
        """builds a hashable cache key for a request, or ``None`` if unsafe."""
        if len(rvals) != 0 and isinstance(rvals[0], EnforceContext):
            # Contexts select a different request/policy/matcher; keying by
            # object identity would be unreliable, so we do not cache these.
            return None
        try:
            key = tuple(rvals)
            hash(key)
        except TypeError:
            return None
        return key

    def _store(self, key, result):
        self._cache[key] = result
        if self._cache_max_size is not None and len(self._cache) > self._cache_max_size:
            # Evict the least-recently-used decision.
            self._cache.popitem(last=False)

    # -- targeted invalidation ---------------------------------------------

    def _invalidate_by_values(self, values):
        """evicts cached requests that share any token value with ``values``."""
        if not self._cache:
            return
        values = {v for v in values if isinstance(v, str)}
        if not values:
            return
        stale = [key for key in self._cache if not values.isdisjoint(key)]
        for key in stale:
            del self._cache[key]

    def _invalidate_for_rule(self, rule):
        if rule:
            self._invalidate_by_values(rule)

    def _invalidate_for_rules(self, rules):
        if not rules:
            return
        affected = set()
        for rule in rules:
            affected.update(v for v in rule if isinstance(v, str))
        self._invalidate_by_values(affected)

    # -- interception of policy mutations ----------------------------------
    #
    # All add/remove/update paths in the management API ultimately call these
    # internal methods, so intercepting them here covers add_policy,
    # remove_policy, the grouping-policy variants, the filtered variants and the
    # rbac helpers built on top of them.

    def _add_policy(self, sec, ptype, rule):
        added = super()._add_policy(sec, ptype, rule)
        if added:
            self._invalidate_for_rule(rule)
        return added

    def _add_policies(self, sec, ptype, rules):
        added = super()._add_policies(sec, ptype, rules)
        if added:
            self._invalidate_for_rules(rules)
        return added

    def _add_policies_ex(self, sec, ptype, rules):
        added = super()._add_policies_ex(sec, ptype, rules)
        # add_policies_ex adds whatever rules were not already present; be
        # conservative and invalidate for every submitted rule.
        self._invalidate_for_rules(rules)
        return added

    def _update_policy(self, sec, ptype, old_rule, new_rule):
        updated = super()._update_policy(sec, ptype, old_rule, new_rule)
        if updated:
            self._invalidate_for_rule(old_rule)
            self._invalidate_for_rule(new_rule)
        return updated

    def _update_policies(self, sec, ptype, old_rules, new_rules):
        updated = super()._update_policies(sec, ptype, old_rules, new_rules)
        if updated:
            self._invalidate_for_rules(old_rules)
            self._invalidate_for_rules(new_rules)
        return updated

    def _update_filtered_policies(self, sec, ptype, new_rules, field_index, *field_values):
        changed = super()._update_filtered_policies(sec, ptype, new_rules, field_index, *field_values)
        if changed:
            self._invalidate_for_rules(new_rules)
            self._invalidate_by_values(field_values)
        return changed

    def _remove_policy(self, sec, ptype, rule):
        removed = super()._remove_policy(sec, ptype, rule)
        if removed:
            self._invalidate_for_rule(rule)
        return removed

    def _remove_policies(self, sec, ptype, rules):
        removed = super()._remove_policies(sec, ptype, rules)
        if removed:
            self._invalidate_for_rules(rules)
        return removed

    def _remove_filtered_policy(self, sec, ptype, field_index, *field_values):
        removed = super()._remove_filtered_policy(sec, ptype, field_index, *field_values)
        if removed:
            # We do not know exactly which rules were removed, only the values
            # they were filtered on, so evict requests sharing those values.
            self._invalidate_by_values(field_values)
        return removed

    def _remove_filtered_policy_returns_effects(self, sec, ptype, field_index, *field_values):
        removed = super()._remove_filtered_policy_returns_effects(sec, ptype, field_index, *field_values)
        if removed:
            self._invalidate_for_rules(removed)
        return removed

    # -- wholesale policy changes clear the whole cache --------------------

    def load_policy(self):
        super().load_policy()
        self.clear_cache()

    def load_filtered_policy(self, filter):
        super().load_filtered_policy(filter)
        self.clear_cache()

    def load_increment_filtered_policy(self, filter):
        super().load_increment_filtered_policy(filter)
        self.clear_cache()

    def clear_policy(self):
        super().clear_policy()
        self.clear_cache()
