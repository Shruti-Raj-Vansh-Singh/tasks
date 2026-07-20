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
        super().__init__(*args, **kwargs)
        self._cache = {}
        self._cache_enabled = True
        self._cache_hits = 0
        self._cache_misses = 0

    def enforce(self, *rvals):
        """decides whether a "subject" can access a "object" with the operation "action",
        input parameters are usually: (sub, obj, act).

        Returns cached result if caching is enabled and the request has been seen before.
        Otherwise evaluates the request using the base Enforcer and caches the result.
        """
        if not self._cache_enabled:
            return super().enforce(*rvals)

        # Create a hashable key from the request values
        cache_key = tuple(rvals)

        # Check cache
        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]

        # Cache miss - evaluate using base enforcer
        self._cache_misses += 1
        result = super().enforce(*rvals)

        # Store in cache
        self._cache[cache_key] = result

        return result

    def enable_cache(self, enabled=True):
        """Enable or disable caching.

        When caching is disabled, the enforcer behaves exactly like the base Enforcer.
        """
        self._cache_enabled = enabled

    def get_cache_stats(self):
        """Returns a JSON-serializable dict with cache statistics.

        Returns:
            dict: A dictionary with keys:
                - enabled (bool): Whether caching is currently enabled
                - hits (int): Number of cache hits since creation
                - misses (int): Number of cache misses since creation
                - size (int): Number of entries currently in the cache
        """
        return {
            "enabled": self._cache_enabled,
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "size": len(self._cache),
        }

    def _invalidate_cache_entries(self, rule):
        """Invalidate cache entries that may be affected by a policy change.

        Only removes entries where the request tuple starts with the same subject
        as the policy rule. This keeps unrelated cache entries warm.

        Args:
            rule: A policy rule as a list (e.g., ["alice", "data1", "read"])
        """
        if not rule or len(rule) == 0:
            return

        # The first element is typically the subject
        rule_subject = rule[0]

        # Find and remove all cache entries where the request starts with this subject
        keys_to_remove = [key for key in self._cache if key[0] == rule_subject]
        for key in keys_to_remove:
            del self._cache[key]

    def add_policy(self, *params):
        """Add a policy rule and invalidate affected cache entries.

        Calls the base add_policy method and then invalidates cache entries
        that may be affected by this change.
        """
        # Handle both add_policy("alice", "data1", "read") and add_policy(["alice", "data1", "read"])
        if len(params) == 1 and isinstance(params[0], list):
            rule = params[0]
        else:
            rule = list(params)

        # Call base implementation
        result = super().add_policy(*params)

        # Invalidate cache entries affected by this rule
        if result:  # Only invalidate if the policy was actually added
            self._invalidate_cache_entries(rule)

        return result

    def add_policies(self, rules):
        """Add multiple policy rules and invalidate affected cache entries."""
        result = super().add_policies(rules)

        # Invalidate cache entries for all rules
        for rule in rules:
            self._invalidate_cache_entries(rule)

        return result

    def add_named_policy(self, ptype, *params):
        """Add a named policy rule and invalidate affected cache entries."""
        # Handle both forms
        if len(params) == 1 and isinstance(params[0], list):
            rule = params[0]
        else:
            rule = list(params)

        result = super().add_named_policy(ptype, *params)

        if result and ptype == "p":  # Only invalidate for regular policies
            self._invalidate_cache_entries(rule)

        return result

    def add_named_policies(self, ptype, rules):
        """Add multiple named policy rules and invalidate affected cache entries."""
        result = super().add_named_policies(ptype, rules)

        if ptype == "p":  # Only invalidate for regular policies
            for rule in rules:
                self._invalidate_cache_entries(rule)

        return result

    def remove_policy(self, *params):
        """Remove a policy rule and invalidate affected cache entries."""
        # Handle both forms
        if len(params) == 1 and isinstance(params[0], list):
            rule = params[0]
        else:
            rule = list(params)

        result = super().remove_policy(*params)

        # Invalidate cache entries affected by this rule
        if result:  # Only invalidate if the policy was actually removed
            self._invalidate_cache_entries(rule)

        return result

    def remove_policies(self, rules):
        """Remove multiple policy rules and invalidate affected cache entries."""
        result = super().remove_policies(rules)

        # Invalidate cache entries for all rules
        for rule in rules:
            self._invalidate_cache_entries(rule)

        return result

    def remove_named_policy(self, ptype, *params):
        """Remove a named policy rule and invalidate affected cache entries."""
        # Handle both forms
        if len(params) == 1 and isinstance(params[0], list):
            rule = params[0]
        else:
            rule = list(params)

        result = super().remove_named_policy(ptype, *params)

        if result and ptype == "p":  # Only invalidate for regular policies
            self._invalidate_cache_entries(rule)

        return result

    def remove_named_policies(self, ptype, rules):
        """Remove multiple named policy rules and invalidate affected cache entries."""
        result = super().remove_named_policies(ptype, rules)

        if ptype == "p":  # Only invalidate for regular policies
            for rule in rules:
                self._invalidate_cache_entries(rule)

        return result

    def remove_filtered_policy(self, field_index, *field_values):
        """Remove filtered policy rules and invalidate affected cache entries."""
        result = super().remove_filtered_policy(field_index, *field_values)

        # For field_index == 0 (subject filter), invalidate all entries for those subjects
        if result and field_index == 0 and len(field_values) > 0:
            subject = field_values[0]
            keys_to_remove = [key for key in self._cache if key[0] == subject]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # For other filters, conservatively invalidate the entire cache
            # since we don't know exactly which entries are affected
            self._cache.clear()

        return result

    def remove_filtered_named_policy(self, ptype, field_index, *field_values):
        """Remove filtered named policy rules and invalidate affected cache entries."""
        result = super().remove_filtered_named_policy(ptype, field_index, *field_values)

        if result and ptype == "p":  # Only invalidate for regular policies
            if field_index == 0 and len(field_values) > 0:
                subject = field_values[0]
                keys_to_remove = [key for key in self._cache if key[0] == subject]
                for key in keys_to_remove:
                    del self._cache[key]
            else:
                # For other filters, conservatively invalidate the entire cache
                self._cache.clear()

        return result

    def update_policy(self, old_rule, new_rule):
        """Update a policy rule and invalidate affected cache entries."""
        result = super().update_policy(old_rule, new_rule)

        if result:
            # Invalidate for both old and new subjects
            self._invalidate_cache_entries(old_rule)
            self._invalidate_cache_entries(new_rule)

        return result

    def update_policies(self, old_rules, new_rules):
        """Update multiple policy rules and invalidate affected cache entries."""
        result = super().update_policies(old_rules, new_rules)

        for old_rule in old_rules:
            self._invalidate_cache_entries(old_rule)
        for new_rule in new_rules:
            self._invalidate_cache_entries(new_rule)

        return result

    def update_named_policy(self, ptype, old_rule, new_rule):
        """Update a named policy rule and invalidate affected cache entries."""
        result = super().update_named_policy(ptype, old_rule, new_rule)

        if result and ptype == "p":
            self._invalidate_cache_entries(old_rule)
            self._invalidate_cache_entries(new_rule)

        return result

    def update_named_policies(self, ptype, old_rules, new_rules):
        """Update multiple named policy rules and invalidate affected cache entries."""
        result = super().update_named_policies(ptype, old_rules, new_rules)

        if ptype == "p":
            for old_rule in old_rules:
                self._invalidate_cache_entries(old_rule)
            for new_rule in new_rules:
                self._invalidate_cache_entries(new_rule)

        return result

    def update_filtered_policies(self, new_rules, field_index, *field_values):
        """Update filtered policies and invalidate affected cache entries."""
        result = super().update_filtered_policies(new_rules, field_index, *field_values)

        if result:
            if field_index == 0 and len(field_values) > 0:
                subject = field_values[0]
                keys_to_remove = [key for key in self._cache if key[0] == subject]
                for key in keys_to_remove:
                    del self._cache[key]
            else:
                self._cache.clear()

        return result

    def update_filtered_named_policies(self, ptype, new_rules, field_index, *field_values):
        """Update filtered named policies and invalidate affected cache entries."""
        result = super().update_filtered_named_policies(ptype, new_rules, field_index, *field_values)

        if result and ptype == "p":
            if field_index == 0 and len(field_values) > 0:
                subject = field_values[0]
                keys_to_remove = [key for key in self._cache if key[0] == subject]
                for key in keys_to_remove:
                    del self._cache[key]
            else:
                self._cache.clear()

        return result
