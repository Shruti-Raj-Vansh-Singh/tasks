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

import json
import os
from unittest import TestCase

import casbin


def get_examples(path):
    examples_path = os.path.split(os.path.realpath(__file__))[0] + "/../examples/"
    return os.path.abspath(examples_path + path)


class TestCachedEnforcer(TestCase):
    def get_enforcer(self):
        return casbin.CachedEnforcer(
            get_examples("basic_model.conf"),
            get_examples("basic_policy.csv"),
        )

    def test_static_decisions_match_base(self):
        e = self.get_enforcer()
        self.assertTrue(e.enforce("alice", "data1", "read"))
        self.assertFalse(e.enforce("alice", "data1", "write"))
        self.assertFalse(e.enforce("bob", "data1", "read"))
        self.assertTrue(e.enforce("bob", "data2", "write"))
        self.assertFalse(e.enforce("bob", "data2", "read"))

    def test_repeated_request_is_served_from_cache(self):
        e = self.get_enforcer()
        self.assertTrue(e.enforce("alice", "data1", "read"))
        self.assertTrue(e.enforce("alice", "data1", "read"))
        self.assertTrue(e.enforce("alice", "data1", "read"))
        stats = e.get_cache_stats()
        self.assertTrue(stats["enabled"])
        self.assertGreaterEqual(stats["hits"], 2)
        self.assertGreaterEqual(stats["misses"], 1)

    def test_get_cache_stats_is_json_serializable(self):
        e = self.get_enforcer()
        e.enforce("alice", "data1", "read")
        stats = e.get_cache_stats()
        json.dumps(stats)
        self.assertIn("enabled", stats)
        self.assertIn("hits", stats)
        self.assertIn("misses", stats)
        self.assertIn("size", stats)

    def test_enable_cache_false_behaves_like_base_enforcer(self):
        e = self.get_enforcer()
        e.enable_cache(False)
        self.assertTrue(e.enforce("alice", "data1", "read"))
        self.assertTrue(e.enforce("alice", "data1", "read"))
        stats = e.get_cache_stats()
        self.assertFalse(stats["enabled"])

    def test_add_policy_is_visible_to_next_enforce(self):
        e = self.get_enforcer()
        self.assertFalse(e.enforce("alice", "data2", "read"))
        # warm the cache with the current (negative) decision
        self.assertFalse(e.enforce("alice", "data2", "read"))
        e.add_policy("alice", "data2", "read")
        self.assertTrue(e.enforce("alice", "data2", "read"))

    def test_remove_policy_is_visible_to_next_enforce(self):
        e = self.get_enforcer()
        self.assertTrue(e.enforce("alice", "data1", "read"))
        # warm the cache with the current (positive) decision
        self.assertTrue(e.enforce("alice", "data1", "read"))
        e.remove_policy("alice", "data1", "read")
        self.assertFalse(e.enforce("alice", "data1", "read"))

    def test_edit_keeps_unrelated_entries_warm(self):
        e = self.get_enforcer()
        # warm two unrelated decisions
        self.assertTrue(e.enforce("alice", "data1", "read"))
        self.assertTrue(e.enforce("bob", "data2", "write"))
        self.assertTrue(e.enforce("alice", "data1", "read"))
        self.assertTrue(e.enforce("bob", "data2", "write"))
        hits_before = e.get_cache_stats()["hits"]
        # edit only alice's permission
        e.remove_policy("alice", "data1", "read")
        # the unrelated bob decision must still be served from the cache
        self.assertTrue(e.enforce("bob", "data2", "write"))
        self.assertGreater(e.get_cache_stats()["hits"], hits_before)
        # and the edited decision is fresh
        self.assertFalse(e.enforce("alice", "data1", "read"))
