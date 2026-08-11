We run pyrate-limiter in front of a public API and I need to tighten up a couple of things before I hand this service off next week. We rate-limit per API key, which works great, but we've been leaking memory: we keep one limiter object per key, and over a few weeks of uptime we've seen millions of distinct keys (lots of one-off clients, scanners, expired keys that never come back). The process just grows until it gets OOM-killed. I need the per-client limiter to keep only a bounded number of clients in memory at any time.

I started a class for this and ran out of time. It's in `pyrate_limiter/bounded_limiter.py` as `BoundedLimiter`, and the `__init__` is already written - it takes a `rate`, a `max_clients`, and an optional `clock`, and it already sets up an `OrderedDict` for the per-client buckets. There are two stubbed methods on it and I need both filled in.

**`try_acquire(client_id, weight=1)`** - the core one. The way I've been picturing it: keep the per-client buckets in the map that's already there (`self._client_buckets`), one `InMemoryBucket([self.rate])` per key, created on first sight of the key. `InMemoryBucket` does all the sliding-window counting for you, so `try_acquire` mostly needs to find (or make) the client's bucket and put the item in. The important new part is the cap: we can't let `self._client_buckets` grow past `self.max_clients`, no matter how many distinct keys show up. How you hold it to that size is your call - I just need memory to stay flat.

Concretely I want:

- `try_acquire(client_id, weight=1)` returns a plain `bool`. `True` means admit, `False` means throttle. It must not block and must not raise when a request is throttled - just return `False`.
- Each client is limited to `rate` on its own (e.g. `Rate(10, Duration.SECOND)` is 10 requests/second per key). One client's traffic is counted separately from another's.
- `len(self._client_buckets)` must stay `<= self.max_clients` at all times. This is the whole point of the change - the box this runs in has a hard memory ceiling and this map was the thing blowing it.
- Weighted requests matter - some endpoints count as 3 or 5 - so pass `weight` through to the bucket.
- Use `self.clock.now()` for timestamps so tests can drive it with a fake clock instead of sleeping. Timestamps are in milliseconds like the rest of the library.

**`try_acquire_request(api_key, forwarded_for="", weight=1)`** - the second stub, same class. Most of our handlers don't have a client id in hand, they have a request; today each of them does its own little "which string do I limit this on" dance at the call site and they've drifted apart. I want one place that answers it:

- A request that presented an `X-API-Key` header is limited per API key. That's the `api_key` argument; it's `None` when the request didn't present one.
- A request with no API key is limited per client address instead. We sit behind nginx so the socket peer is always the proxy - the client address is reported in the `X-Forwarded-For` header, which the handler passes straight through as the raw `forwarded_for` string.
- Same return contract as `try_acquire`: plain `bool`, `True` admit / `False` throttle, doesn't block, doesn't raise on a throttle, and `weight` is passed through the same way.
- It should route through the same limiting machinery as `try_acquire` rather than reimplementing the counting - the memory bound has to hold for these requests too.

Please keep it simple and lean on the library - don't hand-roll a token-bucket algorithm or pull in anything third-party, `InMemoryBucket` and `RateItem` from the package are what you want.

Please also add focused tests in `tests/test_bounded_limiter.py` - there's already a starter file there with a mock clock you can copy the pattern from. Cover a single client hitting its limit, the window refilling after the interval passes, a couple of clients being limited independently, weighted requests, that the number of tracked clients stays within `max_clients` when lots of distinct keys arrive, and the same for the request-facing method: an API key hitting its limit, a request with no API key limited by its address, two different API keys not interfering, and weight going through. The existing test suite should keep passing.
