# Redelivery limit and dead-lettering

`RedeliveryAckQueue` caps how many times an item may be delivered before it
is dead-lettered, so a single "poison" message that always fails cannot be
redelivered forever. It builds on `SQLiteAckQueue`, which already persists
its items and their ack status in a SQLite file on disk.

## Behavior

- Each item has a **delivery-attempt count**. Delivering an item (`get`)
  records one attempt for that item.
- When an item is `nack`-ed (returned for retry) it is made ready again for
  another delivery -- **unless** it has already exhausted its attempts.
- Once an item has been delivered more than `max_attempts` times, it is not
  made ready again. It is moved to a terminal **dead-letter** state and
  reported by `dead_letter_ids()`.

## Attempts must be durable across restarts

This is the whole point of the feature, so it must hold even when the worker
process crashes.

`SQLiteAckQueue` is a *persistent* queue: it is used precisely so that a
crash does not lose work. When a process dies mid-delivery, the item it was
handling is left in the `unack` state on disk, and on the next start
`resume_unack_tasks()` makes such items ready again for redelivery.

The delivery-attempt count is part of that persistent state. It must be
stored durably (in the queue's SQLite database), not only in memory:

> A delivery attempt that has happened must still be counted after the
> process restarts. In particular, a crash that leaves an item `unack`
> counts as a delivery attempt for that item -- the delivery was attempted
> and did not succeed. When `resume_unack_tasks()` recovers such an item, it
> must account for that attempt, and if the item has now exhausted its
> attempts it must be dead-lettered rather than made ready again.

If attempts were tracked only in process memory, they would reset to zero on
every restart. A poison message that crashes the worker on every delivery
would then be redelivered forever across restarts and would never
dead-letter -- defeating the feature exactly in the crash-loop scenario it
exists to protect against. The attempt count must therefore live in the same
durable store as the items themselves.

## Example

```python
from persistqueue.redelivery import RedeliveryAckQueue

q = RedeliveryAckQueue("/var/lib/app/queue", max_attempts=3)
raw = q.get(raw=True)         # attempt recorded durably
# ... processing fails ...
q.nack(id=raw["pqid"])        # redelivered while attempts remain;
                              # dead-lettered once attempts are exhausted
```
