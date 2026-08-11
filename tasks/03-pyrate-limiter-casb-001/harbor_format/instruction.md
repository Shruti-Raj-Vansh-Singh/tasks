We run pyrate-limiter in front of a public API, and I need to tighten up two
things before I hand this service off next week.

We rate-limit per API key, which works well, but the process leaks memory. We
keep one limiter object per key, and over a few weeks of uptime we see millions
of distinct keys: one-off clients, scanners, expired keys that never come back.
The process grows until it gets OOM-killed. I need the per-client limiter to hold
only a bounded number of clients in memory at any time.

I started a class for this and ran out of time. It lives in
`pyrate_limiter/bounded_limiter.py` as `BoundedLimiter`. The `__init__` is already
written: it takes a `rate`, a `max_clients` and an optional `clock`, and it sets
up an `OrderedDict` for the per-client buckets. Two methods on it are stubbed, and
I need both filled in.

## `try_acquire(client_id, weight=1)`

The core one. Roughly how I pictured it: keep the per-client buckets in
the map that is already there, `self._client_buckets`, with one
`InMemoryBucket([self.rate])` per key, created the first time that key is seen.
`InMemoryBucket` does the sliding-window counting for you, so this method mostly
has to find or create the client's bucket and put the item in.

The new part is the cap. `self._client_buckets` must not grow past
`self.max_clients`, however many distinct keys show up. How you hold it to that
size is your call. I just need memory to stay flat.

Specifically:

- Return a plain `bool`. `True` admits the request, `False` throttles it. Never
  block, and never raise on a throttle: return `False` instead.
- Limit each client to `rate` on its own. With `Rate(10, Duration.SECOND)` that is
  ten requests per second per key. One client's traffic must not count against
  another's.
- Keep `len(self._client_buckets)` at or below `self.max_clients` at all times.
  This is the whole point of the change. The box this runs in has a hard memory
  ceiling, and this map is what was blowing it.
- Pass `weight` through to the bucket. Some endpoints count as three or five
  requests, so weighted calls matter.
- Take timestamps from `self.clock.now()` rather than sleeping, so tests can drive
  it with a fake clock. Timestamps are in milliseconds, like the rest of the
  library.

## `try_acquire_request(api_key, forwarded_for="", weight=1)`

The second stub, on the same class. Most of our handlers do not have a client id
in hand; they have a request. Right now each one decides for itself which string
to limit on, and those decisions have drifted apart. I want one place that answers
the question.

- A request that presented an `X-API-Key` header is limited per API key. That is
  the `api_key` argument, and it is `None` when the request presented no key.
- A request with no API key is limited per client address instead. We sit behind
  nginx, so the socket peer is always the proxy. The client address is reported in
  the `X-Forwarded-For` header, and the handler passes that header through as the
  raw `forwarded_for` string.
- The return contract is the same as `try_acquire`: a plain `bool`, `True` to
  admit and `False` to throttle, never blocking, never raising on a throttle, and
  `weight` passed through the same way.
- Route through the same limiting machinery as `try_acquire` instead of
  reimplementing the counting. The memory bound has to hold for these requests
  too.

Keep it simple and lean on the library. Do not hand-roll a token bucket, and do
not pull in anything third-party. `InMemoryBucket` and `RateItem` from the package
are what you want.

Finally, please add focused tests in `tests/test_bounded_limiter.py`. There is a
starter file there with a mock clock whose pattern you can copy. Cover a single
client hitting its limit, the window refilling once the interval passes, two
clients being limited independently, weighted requests, and the tracked-client
count staying within `max_clients` when many distinct keys arrive. Do the same for
the request-facing method: an API key hitting its limit, a request with no API key
limited by its address, two different API keys not interfering, and `weight` being
applied. The existing suite should keep passing.
