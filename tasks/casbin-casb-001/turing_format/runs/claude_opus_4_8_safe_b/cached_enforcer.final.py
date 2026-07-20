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
from casbin.util import generate_g_function, generate_conditional_g_function, util


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
    When a permission rule (section ``p``, ptype ``p``) is added or removed we
    do not throw the whole cache away. Instead we replay the matcher for that
    single rule against every cached request. A rule that does not match a
    request cannot change that request's decision (it only ever contributes an
    "indeterminate" effect), so its cache entry is left warm. Only the entries
    the rule actually matches are dropped, and the next ``enforce`` recomputes
    them. Changes we cannot reason about precisely (grouping/role changes, bulk
    filtered removals, full policy reloads) fall back to a safe full clear so a
    stale decision is never served.

    The cache is bounded (``cache_capacity`` entries, default 10000) and evicts
    least-recently-used entries so a long-running process keeps a stable memory
    footprint.
    """

    def __init__(self, *args, **kwargs):
        capacity = kwargs.pop("cache_capacity", 10000)
        # Set cache state up before super().__init__ so the overridden policy
        # mutators are always safe, even if invoked during initialization.
        self._cache = OrderedDict()
        self._cache_enabled = True
        self._hits = 0
        self._misses = 0
        self._capacity = capacity if capacity and capacity > 0 else None
        super().__init__(*args, **kwargs)

    # -- public cache API ---------------------------------------------------

    def enable_cache(self, enabled=True):
        """turns the decision cache on or off.

        When the cache is disabled the enforcer behaves exactly like the base
        ``Enforcer``: every ``enforce`` call re-runs the matcher and nothing is
        cached. Any existing cached entries are dropped when disabling.
        """
        self._cache_enabled = bool(enabled)
        if not self._cache_enabled:
            self._cache.clear()

    def clear_cache(self):
        """empties the decision cache without touching the hit/miss counters."""
        self._cache.clear()

    def get_cache_stats(self):
        """returns a small JSON-serializable dict describing the cache.

        Keys: ``enabled`` (bool), ``hits`` (int), ``misses`` (int) and ``size``
        (int, the number of cached entries).
        """
        return {
            "enabled": bool(self._cache_enabled),
            "hits": int(self._hits),
            "misses": int(self._misses),
            "size": int(len(self._cache)),
        }

    # -- hot path -----------------------------------------------------------

    def enforce(self, *rvals):
        """decides whether a "subject" can access a "object" with the operation
        "action", input parameters are usually: (sub, obj, act).

        Repeated identical requests are served from the cache instead of
        re-running the matcher.
        """
        if not self._cache_enabled:
            return super().enforce(*rvals)

        # Requests carrying an EnforceContext (or otherwise unhashable values)
        # are not cached; just evaluate them directly.
        if rvals and isinstance(rvals[0], EnforceContext):
            return super().enforce(*rvals)

        try:
            key = tuple(rvals)
            hash(key)
        except TypeError:
            return super().enforce(*rvals)

        cache = self._cache
        if key in cache:
            self._hits += 1
            cache.move_to_end(key)
            return cache[key]

        self._misses += 1
        result = super().enforce(*rvals)
        cache[key] = result
        cache.move_to_end(key)
        if self._capacity is not None and len(cache) > self._capacity:
            cache.popitem(last=False)
        return result

    # -- invalidation on policy edits --------------------------------------

    def _clear_cache(self):
        if self._cache:
            self._cache.clear()

    def _invalidate_for_rules(self, sec, ptype, rules):
        """drops only the cached entries that the changed rules can affect.

        For permission rules (``sec == "p"`` and ``ptype == "p"``) we replay the
        matcher for each changed rule against every cached request and drop the
        entries that match. Anything we cannot reason about precisely, or any
        unexpected error, results in a safe full clear.
        """
        if not self._cache:
            return

        if sec != "p" or ptype != "p":
            # Role/grouping changes and named-policy changes can affect
            # decisions in ways a single-rule replay does not capture; clear
            # everything to stay correct.
            self._clear_cache()
            return

        try:
            to_drop = []
            for key in self._cache:
                for rule in rules:
                    if self._request_hits_rule(key, rule):
                        to_drop.append(key)
                        break
            for key in to_drop:
                self._cache.pop(key, None)
        except Exception:
            # If anything about this model makes a precise decision impossible,
            # never risk serving a stale answer.
            self._clear_cache()

    def _request_hits_rule(self, rvals, rule):
        """returns True if the policy ``rule`` matches request ``rvals``.

        A rule that matches a request contributes to that request's decision, so
        adding or removing it may change the result and the cached entry must be
        dropped. A rule that does not match is irrelevant to the request and its
        entry can stay warm. Mirrors the per-rule evaluation done by
        ``CoreEnforcer.enforce_ex``.
        """
        functions = self.fm.get_functions()
        if "g" in self.model.keys():
            for key, ast in self.model["g"].items():
                if len(self.rm_map) != 0:
                    functions[key] = generate_g_function(ast.rm)
                if len(self.cond_rm_map) != 0:
                    functions[key] = generate_conditional_g_function(ast.cond_rm)

        r_tokens = self.model["r"]["r"].tokens
        p_tokens = self.model["p"]["p"].tokens

        # If the shapes do not line up we cannot reason safely; treat the entry
        # as affected so it gets recomputed.
        if len(r_tokens) != len(rvals) or len(p_tokens) != len(rule):
            return True

        exp_string = self.model["m"]["m"].value
        r_parameters = dict(zip(r_tokens, rvals))
        p_parameters = dict(zip(p_tokens, rule))
        parameters = dict(r_parameters, **p_parameters)

        if util.has_eval(exp_string):
            rule_names = util.get_eval_value(exp_string)
            rules = [util.escape_assertion(p_parameters[rule_name]) for rule_name in rule_names]
            exp_with_rule = util.replace_eval(exp_string, rules)
            expression = self._get_expression(exp_with_rule, functions)
        else:
            expression = self._get_expression(exp_string, functions)

        result = expression.eval(parameters)

        if isinstance(result, bool):
            return result
        if isinstance(result, (int, float)):
            return result != 0
        # Unexpected matcher result type: be conservative and invalidate.
        return True

    # -- policy mutation hooks ---------------------------------------------
    #
    # All add/remove/update paths in the management API funnel through these
    # internal methods with a (sec, ptype, ...) signature, so overriding them
    # keeps a single cache-invalidation point regardless of which public helper
    # the caller used (add_policy, add_grouping_policy, add_role_for_user, ...).

    def _add_policy(self, sec, ptype, rule):
        rule_added = super()._add_policy(sec, ptype, rule)
        if rule_added:
            self._invalidate_for_rules(sec, ptype, [rule])
        return rule_added

    def _add_policies(self, sec, ptype, rules):
        rules_added = super()._add_policies(sec, ptype, rules)
        if rules_added:
            self._invalidate_for_rules(sec, ptype, rules)
        return rules_added

    def _add_policies_ex(self, sec, ptype, rules):
        rules_added = super()._add_policies_ex(sec, ptype, rules)
        if rules_added:
            self._invalidate_for_rules(sec, ptype, rules)
        return rules_added

    def _remove_policy(self, sec, ptype, rule):
        rule_removed = super()._remove_policy(sec, ptype, rule)
        if rule_removed:
            self._invalidate_for_rules(sec, ptype, [rule])
        return rule_removed

    def _remove_policies(self, sec, ptype, rules):
        rules_removed = super()._remove_policies(sec, ptype, rules)
        if rules_removed:
            self._invalidate_for_rules(sec, ptype, rules)
        return rules_removed

    def _remove_filtered_policy(self, sec, ptype, field_index, *field_values):
        rule_removed = super()._remove_filtered_policy(sec, ptype, field_index, *field_values)
        if rule_removed:
            # We do not have the exact removed rules here; clear to stay safe.
            self._clear_cache()
        return rule_removed

    def _remove_filtered_policy_returns_effects(self, sec, ptype, field_index, *field_values):
        removed_rules = super()._remove_filtered_policy_returns_effects(sec, ptype, field_index, *field_values)
        if removed_rules:
            self._invalidate_for_rules(sec, ptype, removed_rules)
        return removed_rules

    def _update_policy(self, sec, ptype, old_rule, new_rule):
        rule_updated = super()._update_policy(sec, ptype, old_rule, new_rule)
        if rule_updated:
            self._invalidate_for_rules(sec, ptype, [old_rule, new_rule])
        return rule_updated

    def _update_policies(self, sec, ptype, old_rules, new_rules):
        rules_updated = super()._update_policies(sec, ptype, old_rules, new_rules)
        if rules_updated:
            self._invalidate_for_rules(sec, ptype, list(old_rules) + list(new_rules))
        return rules_updated

    def _update_filtered_policies(self, sec, ptype, new_rules, field_index, *field_values):
        is_changed = super()._update_filtered_policies(sec, ptype, new_rules, field_index, *field_values)
        if is_changed:
            self._clear_cache()
        return is_changed

    # -- bulk model/policy changes -----------------------------------------

    def load_policy(self):
        """reloads the policy and drops the whole cache (every decision is stale)."""
        super().load_policy()
        self._clear_cache()

    def load_filtered_policy(self, filter):
        """reloads a filtered policy and drops the whole cache."""
        super().load_filtered_policy(filter)
        self._clear_cache()

    def clear_policy(self):
        """clears all policy and drops the whole cache."""
        super().clear_policy()
        self._clear_cache()
