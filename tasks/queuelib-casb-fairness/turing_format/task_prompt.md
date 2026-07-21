We use `queuelib` to schedule work in a broad crawler. One recurring
incident: within a single priority level, one noisy source (domain) produces
thousands of items and keeps getting popped while smaller sources at the same
priority sit and wait for a long time. I'd like a fairness-aware priority
queue in our fork so busy sources can't starve the quiet ones.

I've scaffolded a new class `FairPriorityQueue` in `queuelib/fairqueue.py`.
Each item has an integer `priority` (lower number = higher priority, same
convention as the existing `PriorityQueue`) and a `key` identifying its
source (e.g. a domain). The class is constructed with a
`qfactory(priority, key)` callable that makes an internal FIFO queue for a
bucket. The method bodies currently raise `NotImplementedError` -- please
implement `push`, `pop`, `peek`, and `__len__`.

What it should do:

- `push(obj, priority=0, key="")` enqueues an item under its `(priority,
  key)` bucket.
- `pop()` returns the next item to work on, sharing attention across the
  different sources so one busy source doesn't monopolise the queue.
- `peek()` returns that same next item without removing it; both return
  `None` when the queue is empty.
- `__len__` is the total number of queued items.

`FairPriorityQueue` is meant to slot in wherever the existing `PriorityQueue`
is used, so it should behave like a priority queue as callers already expect,
just with the added fairness across sources. There's a design note at
`docs/fair_priority_queue.md` describing the ordering it should follow -- have
a look at that and at the existing `queuelib/pqueue.py` for the conventions.

Please implement it, add a few focused tests, and keep the existing suite
passing:

    pytest -q

Keep it small and idiomatic -- we'd like to send it upstream.
