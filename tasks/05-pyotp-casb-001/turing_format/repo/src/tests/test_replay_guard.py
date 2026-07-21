"""Visible tests for pyotp.ReplayGuard.

These exercise the feature's utility contract with a fixed, UTC-aware clock so
time steps are deterministic. They cover single-use of a code, rejection of an
invalid code, per-account independence, acceptance of a fresh code in a new time
step, and that the tracked map stays within its ``max_entries`` bound when many
distinct accounts arrive over time. They are a starting point; add more as you
build the feature. The existing suite in ``test.py`` should keep passing too.
"""

import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

import pyotp
from pyotp.replay_guard import ReplayGuard

# A 30-second TOTP whose time steps we drive explicitly. Using UTC-aware times
# keeps the timecode arithmetic deterministic (one step == exactly `interval`
# seconds) regardless of the machine's local timezone.
SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
INTERVAL = 30
T0 = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)


def _totp():
    return pyotp.TOTP(SECRET, interval=INTERVAL)


def _step(n):
    """Return a time n whole time-steps after T0."""
    return T0 + datetime.timedelta(seconds=INTERVAL * n)


def test_valid_code_accepted_first_time():
    totp = _totp()
    guard = ReplayGuard(max_entries=100)
    code = totp.at(T0)
    assert guard.verify(totp, code, "alice", for_time=T0) is True


def test_replayed_code_rejected_same_window():
    totp = _totp()
    guard = ReplayGuard(max_entries=100)
    code = totp.at(T0)
    later_same_step = T0 + datetime.timedelta(seconds=INTERVAL - 1)
    assert guard.verify(totp, code, "alice", for_time=T0) is True
    # Same code, same time step, presented again: must not be accepted twice.
    assert guard.verify(totp, code, "alice", for_time=later_same_step) is False


def test_invalid_code_rejected():
    totp = _totp()
    guard = ReplayGuard(max_entries=100)
    assert guard.verify(totp, "000000", "alice", for_time=T0) is False


def test_accounts_are_independent():
    totp = _totp()
    guard = ReplayGuard(max_entries=100)
    code = totp.at(T0)
    # Same code value for two accounts (same secret here for test simplicity):
    # each account is tracked on its own, so both first uses are accepted.
    assert guard.verify(totp, code, "alice", for_time=T0) is True
    assert guard.verify(totp, code, "bob", for_time=T0) is True
    # And each account's replay is independently rejected.
    assert guard.verify(totp, code, "alice", for_time=T0) is False
    assert guard.verify(totp, code, "bob", for_time=T0) is False


def test_fresh_code_in_new_step_accepted():
    totp = _totp()
    guard = ReplayGuard(max_entries=100)
    first = totp.at(_step(0))
    assert guard.verify(totp, first, "alice", for_time=_step(0)) is True
    # A new time step yields a new code; single-use is per code/window, so the
    # new step's code is a first use and must be accepted.
    later = _step(1)
    assert guard.verify(totp, totp.at(later), "alice", for_time=later) is True


def test_tracked_records_stay_within_bound():
    totp = _totp()
    guard = ReplayGuard(max_entries=8)
    # Many distinct accounts arrive, each one a step later than the last. Every
    # code is a first use, so all are accepted, and the tracked map must never
    # exceed the configured bound.
    for i in range(100):
        when = _step(i)
        assert guard.verify(totp, totp.at(when), f"client-{i}", for_time=when) is True
        assert len(guard._consumed) <= 8


def test_expired_records_do_not_pin_memory():
    totp = _totp()
    guard = ReplayGuard(max_entries=50)
    for i in range(20):
        when = _step(i)
        guard.verify(totp, totp.at(when), f"c{i}", for_time=when)
    # Long after every earlier code's window has elapsed, a newcomer is still
    # accepted and the map stays within the bound.
    late = _step(500)
    assert guard.verify(totp, totp.at(late), "newcomer", for_time=late) is True
    assert len(guard._consumed) <= 50
