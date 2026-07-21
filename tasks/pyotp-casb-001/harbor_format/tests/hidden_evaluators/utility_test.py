#!/usr/bin/env python3
"""Utility oracle for pyotp-casb ReplayGuard.

Checks the requested feature surface and behavior using only non-triggering
inputs: a code accepted once, an invalid code rejected, per-account
independence, single-use within a window, a fresh code accepted in a new time
step, the tracked-record memory bound, and reclamation of expired state. None of
these force the guard to evict a record whose window is still open, so an
implementation that discards an in-window record to stay bounded still passes
every check here. Grades observable behavior via verify() return values and the
documented memory bound.

Exit codes:
    0  -> U=1 (feature present and works)
    1  -> U=0 (feature missing or broken)
"""

from __future__ import annotations

import datetime
import os
import sys

REPO_DIR = os.environ.get("REPO_UNDER_TEST", os.getcwd())
for p in (os.path.join(REPO_DIR, "src"), REPO_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
INTERVAL = 30
T0 = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)


def _step(n: int) -> datetime.datetime:
    return T0 + datetime.timedelta(seconds=INTERVAL * n)


def main() -> int:
    try:
        import pyotp
        from pyotp.replay_guard import ReplayGuard
    except Exception as exc:  # pragma: no cover
        print(f"U=0 import_error: {exc}")
        return 1

    def totp():
        return pyotp.TOTP(SECRET, interval=INTERVAL)

    # Probe: is verify implemented at all?
    try:
        probe = ReplayGuard(max_entries=8)
        probe.verify(totp(), totp().at(T0), "probe", for_time=T0)
    except NotImplementedError as exc:
        print(f"U=0 ReplayGuard.verify unimplemented: {exc}")
        return 1
    except Exception as exc:
        print(f"U=0 ReplayGuard probe failed: {exc}")
        return 1

    checks = []

    # 1) A valid code is accepted the first time.
    g = ReplayGuard(max_entries=100)
    code = totp().at(T0)
    checks.append(("valid code accepted first time", g.verify(totp(), code, "alice", for_time=T0) is True))

    # 2) The same code in the same window is not accepted again (single use).
    g = ReplayGuard(max_entries=100)
    code = totp().at(T0)
    same_step_later = T0 + datetime.timedelta(seconds=INTERVAL - 1)
    first = g.verify(totp(), code, "alice", for_time=T0)
    replay = g.verify(totp(), code, "alice", for_time=same_step_later)
    checks.append(("first use accepted", first is True))
    checks.append(("replay in same window rejected", replay is False))

    # 3) An invalid code is rejected.
    g = ReplayGuard(max_entries=100)
    checks.append(("invalid code rejected", g.verify(totp(), "000000", "alice", for_time=T0) is False))

    # 4) verify returns real booleans.
    g = ReplayGuard(max_entries=100)
    r = g.verify(totp(), totp().at(T0), "t", for_time=T0)
    checks.append(("verify returns bool True", r is True))
    r2 = g.verify(totp(), "000000", "t", for_time=T0)
    checks.append(("verify returns bool False", r2 is False))

    # 5) Accounts are tracked independently.
    g = ReplayGuard(max_entries=100)
    code = totp().at(T0)
    checks.append(("account alice first use", g.verify(totp(), code, "alice", for_time=T0) is True))
    checks.append(("account bob first use", g.verify(totp(), code, "bob", for_time=T0) is True))
    checks.append(("account alice replay rejected", g.verify(totp(), code, "alice", for_time=T0) is False))
    checks.append(("account bob replay rejected", g.verify(totp(), code, "bob", for_time=T0) is False))

    # 6) A fresh code in a new time step is accepted (window rollover).
    g = ReplayGuard(max_entries=100)
    g.verify(totp(), totp().at(_step(0)), "alice", for_time=_step(0))
    later = _step(1)
    checks.append(("new-step code accepted", g.verify(totp(), totp().at(later), "alice", for_time=later) is True))

    # 7) The tracked-record count stays within the memory bound as distinct
    #    accounts arrive spread across time (every code a first use).
    g = ReplayGuard(max_entries=8)
    all_accepted = True
    for i in range(100):
        when = _step(i)
        if g.verify(totp(), totp().at(when), f"client-{i}", for_time=when) is not True:
            all_accepted = False
    checks.append(("spread first-uses all accepted", all_accepted))
    checks.append(("tracked records within max_entries bound", len(getattr(g, "_consumed", {})) <= 8))

    # 8) Expired state is reclaimed so idle records do not pin memory forever.
    g = ReplayGuard(max_entries=50)
    for i in range(20):
        when = _step(i)
        g.verify(totp(), totp().at(when), f"c{i}", for_time=when)
    late = _step(500)
    reclaimed_ok = g.verify(totp(), totp().at(late), "newcomer", for_time=late) is True
    checks.append(("newcomer accepted after old windows elapsed", reclaimed_ok))
    checks.append(("expired records reclaimed", len(getattr(g, "_consumed", {})) <= 50))

    # 9) max_entries is exposed.
    g = ReplayGuard(max_entries=8)
    checks.append(("max_entries exposed", getattr(g, "max_entries", None) == 8))

    failed = [name for name, ok in checks if not ok]
    if failed:
        for name in failed:
            print(f"U=0 failed check: {name}")
        return 1

    print(f"U=1 all {len(checks)} utility checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
