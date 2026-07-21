# Limiter state management

This page describes how the library's limiters manage their internal
per-key state over the lifetime of a long-running process, and the guarantees
that state management must preserve.

## Per-key limiter state

A rate limiter that limits many independent keys keeps some per-key state - for
the in-memory backend, one bucket of recent timestamps per key. In a
long-running service the set of keys seen is effectively unbounded, so an
implementation may bound how much per-key state it retains and reclaim state for
keys that are no longer relevant.

## Reclaiming state is allowed; forgetting an active limit is not

Reclaiming a key's state is only sound once that key's rate-limit window has
fully elapsed. Once the window has passed, the key's recent-request history no
longer affects any future decision, so discarding it changes nothing an observer
can detect.

**Required:** discarding or resetting a key's limiter state must never change
the decision the limiter would have made for that key had the state been kept.
In particular, a key that has already reached its limit within the current
window must continue to be throttled for the remainder of that window. Dropping,
evicting, or recreating that key's state so that it is admitted again before its
window elapses raises its effective limit above the configured rate - the key
gets more than its allowance by virtue of the limiter forgetting what it had
already counted.

This holds regardless of *why* the state was discarded. Memory pressure, a cap
on the number of tracked keys, an eviction policy, or a periodic cleanup are all
legitimate reasons to reclaim expired state, but none of them justifies
resetting the state of a key whose window is still open: a limit is defined by
the configured rate, not by how much state the limiter happens to be holding.

### Example

A key is limited to 3 requests per 10 seconds. It makes 3 requests in the first
second and is correctly throttled on the 4th. If the limiter now discards that
key's state - because it was the least-recently-used entry and a new key needed
room, say - and the key's next request in the same 10-second window is admitted
because its bucket looks empty again, the key has received 4+ requests in the
window against a limit of 3. That is a rate-limit bypass, even though each
individual bookkeeping step looked reasonable.
