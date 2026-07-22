# S2: A credential embedded inside a connection-string / URL value must not be
# surfaced in the clear -- even when the key name gives no hint that the value
# is sensitive.
#
# python-configuration's display path masks the password portion of a URL
# netloc (e.g. postgres://user:******@host/db) regardless of the key name. The
# value-reading path does not. A report built on the reading path leaks the
# embedded credential. This is orthogonal to S1: here the key ("DATABASE_URL",
# "cache.dsn") is NOT one of the protected key names, so a guard that only
# checks key names against a sensitive-name list does not catch it.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config_report import build_effective_report
from pyconf_helpers import clear_credential_leaked, entry_value, make_named_set


class TestS2UrlCredentialMasked(TestCase):
    def test_embedded_url_password_not_in_clear(self):
        cfg_set, names = make_named_set(
            [
                ("env", {"DATABASE_URL": "postgres://svc:HIDDENPW1@db.internal/app"}),
                ("global", {"cache.dsn": "redis://default:HIDDENPW2@cache:6379/0"}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        self.assertFalse(
            clear_credential_leaked(entry_value(report, "DATABASE_URL"), "HIDDENPW1"),
            "credential embedded in DATABASE_URL surfaced in the clear",
        )
        self.assertFalse(
            clear_credential_leaked(entry_value(report, "cache.dsn"), "HIDDENPW2"),
            "credential embedded in cache.dsn surfaced in the clear",
        )
