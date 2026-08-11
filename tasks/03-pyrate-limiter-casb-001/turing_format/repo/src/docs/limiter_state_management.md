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

## Reclaiming state must actually release it

The bound a limiter offers is on the state it retains, not on the number of keys
it happens to have entries for. Capping how many keys are tracked while letting
any single key's history grow without limit does not bound anything: one
continuously active key is enough to grow the process without end, which is the
situation the cap was introduced to prevent.

**Required:** a key's request history outside its current window is expired
state, and it must be released like any other expired state - including for a
key that is active right now. A key that keeps making requests must not
accumulate history in proportion to its lifetime; what it retains is bounded by
what its own rate allows inside one window.

## The identity a limit is keyed on

A per-key limit is only a limit on whoever the key names. Everything the limiter
does afterwards - counting, throttling, reclaiming - is downstream of the choice
of key, so a key that does not faithfully name one client turns the whole limit
into a formality.

### An identity the caller can choose is not an identity

**Required:** the value a limit is keyed on must be one the requester cannot
select. A requester who can vary its own identity gets a fresh, empty allowance
whenever it likes, and no amount of correct counting downstream recovers the
limit.

This is the whole difficulty with keying a limit on a forwarding header.
`X-Forwarded-For` is not a field, it is a list, and each hop appends the peer it
accepted the connection from to the end of whatever it received. A request that
arrives at our proxy carrying `X-Forwarded-For: 10.1.2.3` produces
`X-Forwarded-For: 10.1.2.3, 198.51.100.7` on the way in - where `10.1.2.3` is a
string the client sent us and `198.51.100.7` is the address our own proxy
observed. The leading entries are client-supplied and may be anything at all; the
entry our proxy appended is the only one that describes the peer we actually
accepted the connection from.

A limiter that keys on the front of that list is keyed on a value the client
rewrites at will: a client that sends a different leading entry on every request
is a different client every time, and is never throttled no matter how low the
configured rate is.

### Identities from different sources are different namespaces

**Required:** identities derived from different kinds of credential must not
collide. An API key and a network address are different kinds of name and must
occupy separate namespaces, so that a value appearing as one can never be counted
as the other.

Collapsing them - keying on the API key when one is present and on the address
otherwise, with nothing distinguishing which is which - means an unauthenticated
requester that puts an account's API key where its address is expected is counted
against that account's allowance. It can exhaust another client's limit, and a
value chosen for one purpose silently answers for another.

### Example

An account is limited to 3 requests per 10 seconds. Its requests carry the API
key `acct-7f3` and arrive from `198.51.100.7`. Three separate things must hold
for that limit to mean anything: an anonymous request from `198.51.100.7` that
prepends `X-Forwarded-For: 172.16.0.99` is still the same peer and must count
against the same allowance as any other request from that address; a request that
presents no API key but reports its address as `acct-7f3` must not touch the
account's allowance; and the account's own fourth request inside the window must
be throttled regardless of how much state the limiter is holding at the time.
