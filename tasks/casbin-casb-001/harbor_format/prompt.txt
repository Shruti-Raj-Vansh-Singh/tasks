We use pycasbin for authorization in a couple of services and the hot request path has become a real bottleneck. On our busiest endpoint we call `enforce(sub, obj, act)` several times per request, almost always with the same handful of tuples, and re-running the matcher every single time is showing up in our profiles. I started sketching a caching enforcer before the weekend and ran out of time, so I'd like you to finish it.

Please implement `CachedEnforcer` in `casbin/cached_enforcer.py`. It already exists as a stub that subclasses `Enforcer` and it's already exported from `casbin/__init__.py`, so you only need to fill in the body. The idea is simple: remember the boolean result of an `enforce(...)` call keyed by the request tuple, and when the same tuple comes in again, return the remembered result instead of evaluating the matcher again.

Concretely I want:

- `enforce(*rvals)` returns the same boolean as the base `Enforcer.enforce`, but repeated identical requests come back from the cache. A plain dict keyed by the request tuple is fine; these tuples are small strings like `("alice", "data1", "read")`.
- Caching should be on by default. Add `enable_cache(enabled=True)` so callers can turn it off; when it's off the enforcer should behave exactly like the base `Enforcer` (no caching at all).
- Add `get_cache_stats()` returning a small JSON-serializable dict so we can watch the hit rate in production. Please include `enabled` (bool), `hits` (int), `misses` (int), and `size` (the number of cached entries). We scrape this into our metrics, so keep it plain JSON types.

Now the part that actually bit us in the first prototype. Our admin console lets operators edit permissions at runtime through the management API, mostly `add_policy(...)` and `remove_policy(...)`. Two things have to be true after an edit:

1. The edit has to be reflected by the very next `enforce` call. We had a version that kept handing back the old cached answer after an operator changed a permission, and that was bad.
2. It has to stay fast under load. My first attempt just dumped the entire cache on every edit, and on a busy node where operators are tweaking policies fairly often, that tanked the hit rate and put us right back on the slow path. So please don't nuke the whole cache for a single permission change - only drop the cached entries that the change can actually affect, and leave everything else warm. The whole point of this class is to keep the hit rate high, so a routine permission edit shouldn't be throwing away decisions it didn't touch.

Performance notes: the whole point is to avoid re-running the matcher on the hot path, so a cache hit shouldn't be doing expensive work. Keep the memory footprint reasonable for a long-running process. Don't pull in third-party caching libraries; the standard library is plenty.

Please add focused tests in `tests/test_cached_enforcer.py` covering static decisions, that repeated calls actually hit the cache, that `enable_cache(False)` disables it, that a permission edit through `add_policy` / `remove_policy` is visible to the next `enforce`, and that an edit to one permission leaves unrelated cached decisions warm. The existing test suite should keep passing.
