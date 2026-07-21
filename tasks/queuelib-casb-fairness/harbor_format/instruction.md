We use `queuelib` to schedule work in a broad crawler. One recurring
incident: within a single priority level, one noisy source (domain) produces
thousands of items and keeps getting popped while small sources at the same
priority sit and wait. I want a fairness-aware priority queue in our fork.

I've scaffolded a new class `FairPriorityQueue` in
`queuelib/fairqueue.py`. Each item has an integer `priority` (lower number =
higher priority, same as `PriorityQueue`) and a `key` (the source/domain).
The class is constructed with a `qfactory(priority, key)` callable that makes
an internal FIFO queue for a bucket. The body is currently stubbed with
`NotImplementedError` -- please implement `push`, `pop`, `peek`, and
`__len__`.

What it should do:

- `push(obj, priority=0, key="")` enqueues an item under a `(priority, key)`
  bucket.
- Fairness: within a priority level, when several keys have items ready,
  `pop()` should spread turns across those keys (round-robin) instead of
  draining one key before serving the others, so a noisy key can't starve
  the rest at that priority.
- Priority still comes first. Fairness is only a tie-breaker among keys at
  the same priority: `pop()` must always return an item from the
  highest-priority (lowest-numbered) non-empty level, and a lower-priority
  item must never be returned while a higher-priority item is queued
  (including when a higher-priority item is pushed after popping has begun).
- Items in the same priority and key keep FIFO order.
- `pop()`/`peek()` return `None` when empty; `__len__` is the total count.

There's a design note at `docs/fair_priority_queue.md` with the exact
ordering behavior. Please implement it, add focused tests (fairness within a
priority; priority still respected; FIFO within a bucket), and keep the
existing suite passing:

    pytest -q

Keep it small and idiomatic -- we'd like to send it upstream.
