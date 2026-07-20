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

import threading
from collections import OrderedDict

from casbin.core_enforcer import EnforceContext
from casbin.enforcer import Enforcer

# Default upper bound on the number of remembered decisions. The cache keeps
# small string tuples, so this keeps the footprint modest for a long-running
# process while still comfortably covering the "handful of hot tuples" case.
DEFAULT_CACHE_CAPACITY = 10000

# Sentinel used to distinguish "not cached" from a cached ``False`` decision.
_MISSING = object()


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
    Adding or removing a single ``p`` (permission) rule can only change the
    decision for a request that actually *matches* that rule -- a
    ``some(where p.eft == allow)`` style effector simply ignores rules a request
    does not match, so a non-matching rule contributes nothing either way. For
    the equality / RBAC / keymatch matchers that authorization uses in practice,
    any request that matches a rule shares at least one field value with it
    (its object and/or action). We therefore drop only the cached requests that
    share a field value with the changed rule and leave every other decision
    warm.

    Role-graph edits (the ``g`` section) and bulk / filtered / reload operations
    can change decisions for requests that share no token with the edited rule
    (e.g. through a transitive role such as ``g, admin, superadmin``). Those are
    less common than the permission edits described above, so rather than risk
    serving a stale decision we conservatively clear the whole cache for them.
    Correctness -- the edit being visible to the very next ``enforce`` -- always
    wins over keeping the cache warm.

    An optional ``cache_capacity`` keyword argument bounds the number of
    remembered decisions (LRU eviction). Pass ``cache_capacity=None`` for an
    unbounded cache.
    """

    def __init__(self, *args, **kwargs):
        cache_capacity = kwargs.pop("cache_capacity", DEFAULT_CACHE_CAPACITY)

        # Set the cache state up *before* delegating to the base initializer so
        # that any policy loading performed during construction finds a usable
        # (empty) cache.
        self._cache_lock = threading.RLock()
        self._cache = OrderedDict()
        self._cache_enabled = True
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_capacity = cache_capacity

        super().__init__(*args, **kwargs)

    # ------------------------------------------------------------------ #
    # public cache API
    # ------------------------------------------------------------------ #
    def enable_cache(self, enabled=True):
        """turns the decision cache on or off.

        When caching is disabled the enforcer behaves exactly like the base
        ``Enforcer``: ``enforce`` neither reads from nor writes to the cache.
        Toggling the flag also drops any remembered decisions so that a later
        re-enable can never serve a decision that predates a policy change made
        while caching was off.
        """
        with self._cache_lock:
            self._cache_enabled = bool(enabled)
            self._cache.clear()

    def get_cache_stats(self):
        """returns a small JSON-serializable dict describing the cache.

        Keys: ``enabled`` (bool), ``hits`` (int), ``misses`` (int) and
        ``size`` (int, the number of cached entries).
        """
        with self._cache_lock:
            return {
                "enabled": bool(self._cache_enabled),
                "hits": int(self._cache_hits),
                "misses": int(self._cache_misses),
                "size": len(self._cache),
            }

    def clear_cache(self):
        """drops every remembered decision, leaving the hit/miss counters intact."""
        self._clear_cache()

    # ------------------------------------------------------------------ #
    # enforce
    # ------------------------------------------------------------------ #
    def enforce(self, *rvals):
        """decides whether a "subject" can access an "object" with the operation
        "action", serving repeated identical requests from the cache.
        """
        if not self._cache_enabled:
            return super().enforce(*rvals)

        key = self._make_key(rvals)
        if key is None:
            # Requests we cannot key safely (e.g. an EnforceContext or an
            # unhashable argument) simply bypass the cache.
            return super().enforce(*rvals)

        with self._cache_lock:
            cached = self._cache.get(key, _MISSING)
            if cached is not _MISSING:
                # Mark as most-recently-used and return without touching the matcher.
                self._cache.move_to_end(key)
                self._cache_hits += 1
                return cached
            self._cache_misses += 1

        # Evaluate outside the lock so the (potentially expensive) matcher run
        # never blocks other threads reading the cache.
        result = super().enforce(*rvals)

        with self._cache_lock:
            self._cache[key] = result
            self._cache.move_to_end(key)
            if self._cache_capacity is not None and len(self._cache) > self._cache_capacity:
                # Evict the least-recently-used entry.
                self._cache.popitem(last=False)

        return result

    @staticmethod
    def _make_key(rvals):
        """builds a hashable cache key from a request, or ``None`` to bypass."""
        if len(rvals) == 0:
            return None
        if isinstance(rvals[0], EnforceContext):
            return None
        try:
            key = tuple(rvals)
            hash(key)
        except TypeError:
            return None
        return key

    # ------------------------------------------------------------------ #
    # cache maintenance helpers
    # ------------------------------------------------------------------ #
    def _clear_cache(self):
        with self._cache_lock:
            self._cache.clear()

    def _invalidate_matching_values(self, values):
        """drops cached requests that share a field value with a changed rule."""
        value_set = set(values)
        if not value_set:
            return
        with self._cache_lock:
            if not self._cache:
                return
            doomed = [key for key in self._cache if value_set.intersection(key)]
            for key in doomed:
                del self._cache[key]

    def _on_policy_change(self, sec, rules):
        """invalidates the cache after a policy change.

        ``rules`` is the list of rules that were actually added or removed.
        """
        if sec == "p":
            values = set()
            for rule in rules:
                values.update(rule)
            self._invalidate_matching_values(values)
        else:
            # Grouping / role changes can affect requests that share no token
            # with the edited rule (transitive roles), so be conservative.
            self._clear_cache()

    # ------------------------------------------------------------------ #
    # internal policy-mutation hooks
    #
    # Every management-API edit funnels through these InternalEnforcer methods,
    # so overriding them keeps the cache consistent no matter which public
    # method the caller used.
    # ------------------------------------------------------------------ #
    def _add_policy(self, sec, ptype, rule):
        changed = super()._add_policy(sec, ptype, rule)
        if changed:
            self._on_policy_change(sec, [rule])
        return changed

    def _add_policies(self, sec, ptype, rules):
        changed = super()._add_policies(sec, ptype, rules)
        if changed:
            self._on_policy_change(sec, rules)
        return changed

    def _add_policies_ex(self, sec, ptype, rules):
        changed = super()._add_policies_ex(sec, ptype, rules)
        if changed:
            self._on_policy_change(sec, rules)
        return changed

    def _remove_policy(self, sec, ptype, rule):
        changed = super()._remove_policy(sec, ptype, rule)
        if changed:
            self._on_policy_change(sec, [rule])
        return changed

    def _remove_policies(self, sec, ptype, rules):
        changed = super()._remove_policies(sec, ptype, rules)
        if changed:
            self._on_policy_change(sec, rules)
        return changed

    def _update_policy(self, sec, ptype, old_rule, new_rule):
        changed = super()._update_policy(sec, ptype, old_rule, new_rule)
        if changed:
            self._on_policy_change(sec, [old_rule, new_rule])
        return changed

    def _update_policies(self, sec, ptype, old_rules, new_rules):
        changed = super()._update_policies(sec, ptype, old_rules, new_rules)
        if changed:
            self._on_policy_change(sec, list(old_rules) + list(new_rules))
        return changed

    def _remove_filtered_policy_returns_effects(self, sec, ptype, field_index, *field_values):
        removed = super()._remove_filtered_policy_returns_effects(sec, ptype, field_index, *field_values)
        if removed:
            self._on_policy_change(sec, removed)
        return removed

    def _remove_filtered_policy(self, sec, ptype, field_index, *field_values):
        # The removed rules are not returned here, so we cannot scope the
        # invalidation precisely; clear the whole cache to stay correct.
        changed = super()._remove_filtered_policy(sec, ptype, field_index, *field_values)
        if changed:
            self._clear_cache()
        return changed

    def _update_filtered_policies(self, sec, ptype, new_rules, field_index, *field_values):
        changed = super()._update_filtered_policies(sec, ptype, new_rules, field_index, *field_values)
        if changed:
            self._clear_cache()
        return changed

    # ------------------------------------------------------------------ #
    # wholesale policy/model changes
    # ------------------------------------------------------------------ #
    def load_policy(self):
        super().load_policy()
        self._clear_cache()

    def load_filtered_policy(self, filter):
        super().load_filtered_policy(filter)
        self._clear_cache()

    def load_increment_filtered_policy(self, filter):
        super().load_increment_filtered_policy(filter)
        self._clear_cache()

    def clear_policy(self):
        super().clear_policy()
        self._clear_cache()

    def build_role_links(self):
        super().build_role_links()
        self._clear_cache()
