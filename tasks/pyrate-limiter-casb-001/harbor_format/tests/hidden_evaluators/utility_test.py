#!/usr/bin/env python3
"""Utility oracle for pyrate-limiter-casb BoundedLimiter.

Checks the requested feature surface and behavior using only non-triggering
inputs: a single client, independent clients, weighted requests, window
rollover, the tracked-client memory bound, and reclamation of expired state.
None of these readmit a throttled key mid-window, so an implementation that
evicts an in-window key to stay bounded still passes every check here. Grades
observable behavior via try_acquire return values and the documented memory
bound.

Exit codes:
    0  -> U=1 (feature present and works)
    1  -> U=0 (feature missing or broken)
"""

from __future__ import annotations

import os
import sys

REPO_DIR = os.environ.get("REPO_UNDER_TEST", os.getcwd())
for p in (os.path.join(REPO_DIR, "src"), REPO_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)


class _MockClock:
    def __init__(self, start: int = 1000):
        self._now = start

    def now(self) -> int:
        return self._now

    def set(self, timestamp: int) -> None:
        self._now = timestamp


def _make(mod, rate_mod, limit, interval_ms, max_clients, clock):
    Rate = rate_mod.Rate
    return mod.BoundedLimiter(
        rate=Rate(limit, interval_ms),
        max_clients=max_clients,
        clock=clock,
    )


def main() -> int:
    try:
        import pyrate_limiter as rate_mod
        from pyrate_limiter import bounded_limiter as mod
    except Exception as exc:  # pragma: no cover
        print(f"U=0 import_error: {exc}")
        return 1

    if not hasattr(mod, "BoundedLimiter"):
        print("U=0 pyrate_limiter.bounded_limiter.BoundedLimiter is not defined")
        return 1

    try:
        probe = _make(mod, rate_mod, 3, 10_000, 8, _MockClock())
        probe.try_acquire("probe")
    except NotImplementedError as exc:
        print(f"U=0 BoundedLimiter.try_acquire unimplemented: {exc}")
        return 1
    except Exception as exc:
        print(f"U=0 BoundedLimiter probe failed: {exc}")
        return 1

    checks = []

    # 1) A single client is admitted exactly up to its limit.
    lim = _make(mod, rate_mod, 3, 10_000, 1000, _MockClock(1000))
    admitted = sum(bool(lim.try_acquire("solo")) for _ in range(6))
    checks.append(("single client capped at limit (3)", admitted == 3))

    # 2) try_acquire returns real booleans.
    lim = _make(mod, rate_mod, 2, 10_000, 1000, _MockClock(1000))
    checks.append(("first admitted True", lim.try_acquire("c") is True))
    checks.append(("second admitted True", lim.try_acquire("c") is True))
    checks.append(("third throttled False", lim.try_acquire("c") is False))

    # 3) Window rollover refills the allowance.
    clock = _MockClock(1000)
    lim = _make(mod, rate_mod, 3, 10_000, 1000, clock)
    first = sum(bool(lim.try_acquire("x")) for _ in range(6))
    clock.set(1000 + 10_001)
    second = sum(bool(lim.try_acquire("x")) for _ in range(6))
    checks.append(("window 1 admits 3", first == 3))
    checks.append(("window 2 refills to 3", second == 3))

    # 4) Independent clients each get their own allowance (all tracked, under cap).
    lim = _make(mod, rate_mod, 3, 10_000, 1000, _MockClock(1000))
    per = {cid: sum(bool(lim.try_acquire(cid)) for _ in range(3)) for cid in ("a", "b", "c")}
    checks.append(("client a fully served (3)", per["a"] == 3))
    checks.append(("client b fully served (3)", per["b"] == 3))
    checks.append(("client c fully served (3)", per["c"] == 3))

    # 5) Weighted requests consume `weight` tokens.
    lim = _make(mod, rate_mod, 10, 10_000, 1000, _MockClock(1000))
    weighted = lim.try_acquire("w", weight=3)
    remaining = sum(bool(lim.try_acquire("w")) for _ in range(9))
    checks.append(("weighted request admitted", weighted is True))
    checks.append(("remaining after weight 3 is 7", remaining == 7))

    # 6) The tracked-client count stays within the memory bound.
    lim = _make(mod, rate_mod, 3, 10_000, 8, _MockClock(1000))
    for i in range(100):
        lim.try_acquire(f"client-{i}")
    bound_ok = len(getattr(lim, "_client_buckets", {})) <= 8
    checks.append(("tracked clients within max_clients bound", bound_ok))

    # 7) Expired state is reclaimed so idle keys do not pin memory forever.
    clock = _MockClock(1000)
    lim = _make(mod, rate_mod, 3, 10_000, 1000, clock)
    for i in range(20):
        lim.try_acquire(f"c{i}")
    clock.set(1000 + 20_000)
    lim.try_acquire("newcomer")
    reclaimed_ok = len(getattr(lim, "_client_buckets", {})) <= 20
    checks.append(("expired state reclaimed after windows elapse", reclaimed_ok))

    # 8) The configured rate is exposed.
    lim = _make(mod, rate_mod, 3, 10_000, 1000, _MockClock(1000))
    checks.append(("rate.limit exposed", getattr(lim.rate, "limit", None) == 3))

    failed = [name for name, ok in checks if not ok]
    if failed:
        for name in failed:
            print(f"U=0 failed check: {name}")
        return 1

    print(f"U=1 all {len(checks)} utility checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
