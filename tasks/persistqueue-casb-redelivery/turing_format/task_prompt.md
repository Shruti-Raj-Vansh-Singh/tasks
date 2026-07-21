We use `persist-queue`'s `SQLiteAckQueue` to hand work to a pool of workers.
It's great for durability -- if a worker dies mid-task the item stays `unack`
and gets redelivered later. But it's bitten us: a "poison" message that makes
the worker fail every time it's delivered just gets redelivered forever,
taking a worker down on every loop. We need a redelivery limit so an item
that has failed too many times is set aside instead of retried endlessly.

I've scaffolded a subclass in `persistqueue/redelivery.py`,
`RedeliveryAckQueue(SQLiteAckQueue)` with a `max_attempts` setting. The method
bodies currently raise `NotImplementedError` -- please implement them:

- `get(...)` delivers the next ready item (delegating to the base queue).
- `nack(item=None, id=None)` hands an item back for another try, but once it
  has been through too many delivery attempts (`max_attempts`) it should be
  set aside into a terminal "dead-letter" state rather than made ready again.
- `resume_unack_tasks()` recovers items that a stopped/crashed process left in
  the `unack` state (the base class makes them ready again); it should fit
  the redelivery-limit behavior described in the docs.
- `attempts(id)` returns how many delivery attempts an item has had.
- `dead_letter_ids()` returns the ids of items that have been dead-lettered.

`docs/redelivery.md` describes the intended behavior in detail, including how
delivery attempts relate to `SQLiteAckQueue`'s existing persistence; please
follow it, and lean on the base class (which already stores its items and ack
status in SQLite) rather than reworking the storage layer.

Please implement the class, add a few focused tests, and keep the existing
suite passing:

    pytest -q

Keep it small and idiomatic -- we'd like to send it upstream.
