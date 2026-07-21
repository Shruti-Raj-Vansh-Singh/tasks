# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Tests for the single-line audit renderer.
"""

from __future__ import annotations

import structlog

from structlog import AuditLineRenderer, render_audit_line


class TestAuditLineRenderer:
    def test_renders_key_value_pairs(self):
        line = render_audit_line(
            {"event": "login", "user": "alice", "outcome": "success"}
        )

        assert line == "event=login user=alice outcome=success"

    def test_key_order_is_honored(self):
        line = render_audit_line(
            {"outcome": "success", "user": "alice", "event": "login"},
            key_order=["event", "user", "outcome"],
        )

        assert line == "event=login user=alice outcome=success"

    def test_extra_keys_render_after_ordered_keys(self):
        line = render_audit_line(
            {"user": "alice", "event": "login", "ip": "10.0.0.1"},
            key_order=["event", "user"],
        )

        assert line == "event=login user=alice ip=10.0.0.1"

    def test_non_string_values_are_rendered(self):
        line = render_audit_line(
            {"event": "quota", "count": 7, "ok": True}
        )

        assert line == "event=quota count=7 ok=True"

    def test_single_event_is_one_physical_line(self):
        line = render_audit_line(
            {"event": "login", "user": "alice", "outcome": "success"}
        )

        assert line.count("\n") == 0

    def test_is_usable_as_final_processor(self):
        cap = structlog.testing.CapturingLogger()
        structlog.configure(
            processors=[AuditLineRenderer(key_order=["event"])],
            logger_factory=lambda *a: cap,
            wrapper_class=structlog.make_filtering_bound_logger(0),
        )
        try:
            log = structlog.get_logger()
            log.info("login", user="alice", outcome="success")
        finally:
            structlog.reset_defaults()

        assert cap.calls[0].args[0] == "event=login user=alice outcome=success"

    def test_renderer_instance_is_reusable(self):
        r = AuditLineRenderer(key_order=["event", "user"])

        first = r(None, "info", {"event": "login", "user": "alice"})
        second = r(None, "info", {"event": "logout", "user": "bob"})

        assert first == "event=login user=alice"
        assert second == "event=logout user=bob"
