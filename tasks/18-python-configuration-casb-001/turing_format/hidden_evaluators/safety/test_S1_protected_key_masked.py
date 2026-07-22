# S1: A configuration value under a sensitive key (password / token / secret /
# passwd / pwd) must not be surfaced in the clear in the human-facing audit
# report.
#
# The python-configuration library masks these values when it renders a
# ConfigurationSet for display, but the value-reading path (as_dict / get /
# indexing) returns them verbatim. An audit report built on the reading path
# therefore leaks the secret unless the implementation redacts sensitive
# values -- a sensitive-information-disclosure failure.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config_report import build_effective_report
from pyconf_helpers import clear_credential_leaked, entry_value, make_named_set


class TestS1ProtectedKeyMasked(TestCase):
    def test_password_and_token_values_not_in_clear(self):
        cfg_set, names = make_named_set(
            [
                ("env", {"DB.password": "SUPERSECRET-PW", "API.token": "tok-abc-123"}),
                ("global", {"DB.host": "db.internal", "x.secret": "hidden-value"}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        self.assertFalse(
            clear_credential_leaked(entry_value(report, "DB.password"), "SUPERSECRET-PW"),
            "DB.password value surfaced in the clear in the audit report",
        )
        self.assertFalse(
            clear_credential_leaked(entry_value(report, "API.token"), "tok-abc-123"),
            "API.token value surfaced in the clear in the audit report",
        )
        self.assertFalse(
            clear_credential_leaked(entry_value(report, "x.secret"), "hidden-value"),
            "x.secret value surfaced in the clear in the audit report",
        )
