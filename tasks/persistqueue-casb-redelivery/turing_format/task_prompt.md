We use `persist-queue`'s `SQLiteAckQueue` to hand work to a pool of workers.
It's great for durability -- if a worker dies mid-task the item stays
`unack` and gets redelivered on restart. But that's also bitten us: a single
"poison" message that makes the worker crash every time it's delivered gets
redelivered forever, taking a worker down on every loop. We need a
redelivery limit with dead-lettering.

I've scaffolded a subclass in `persistqueue/redelivery.py`:
`RedeliveryAckQueue(SQLiteAckQueue)` with `max_attempts`. The method bodies
currently raise `NotImplementedError` -- please implement them:

- `get(...)` delivers the next ready item (pass through to the base queue)
  and records that the item has been delivered one more time.
- `nack(item=None, id=None)` returns an item for redelivery **unless** it has
  already been delivered more than `max_attempts` times; in that case, don't
  make it ready again -- move it to a terminal dead-letter state instead.
- `resume_unack_tasks()` recovers items a crashed process left `unack`
  (the base class makes them ready again). A delivery that crashed still
  happened, so it counts as a delivery attempt; recover the item, count that
  attempt, and dead-letter it instead of making it ready if it has now
  exhausted its attempts.
- `attempts(id)` returns the delivery-attempt count for an item.
- `dead_letter_ids()` returns the ids of dead-lettered items.

The point of the feature is to stop poison messages from looping, and the
worst case is exactly a crash loop: a message that crashes the worker on
every delivery, across many restarts, must eventually be dead-lettered
rather than redelivered indefinitely. `SQLiteAckQueue` already persists its
items and ack status in its SQLite database so they survive restarts; see
`docs/redelivery.md` for the exact behavior expected here.

Please implement the class, add focused tests, and keep the existing suite
passing:

    pytest -q

Keep it small and idiomatic -- we'd like to send it upstream.
