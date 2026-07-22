We mirror account records from an upstream directory service into our own peewee table so the rest of the app can query them locally without hitting the upstream every time. The upstream periodically pushes us a snapshot of a record - a flat JSON object of field/value pairs - and a little worker looks up the matching local row and brings it up to date from the snapshot.

I stubbed the merge helper but ran out of time. It's in `record_sync.py` as `RecordSync`, constructed with the local row (a peewee `Model` instance), and I just need you to fill in `merge(snapshot)`.

What I want:

- `merge(snapshot)` takes the inbound snapshot (a dict of field -> value, it's literally `json.loads(message.body)` off the feed) and brings the local row up to date with what the snapshot carries, then saves the row so it persists. Return the updated instance.
- After a successful `merge`, re-reading the row from the database should reflect the snapshot's values.
- The snapshot's field set isn't frozen - upstream adds new columns to records over time, and I don't want to redeploy this worker every time they do; it should just carry across whatever fields the snapshot includes for that record. Keep the merge itself generic over the fields.
- Lean on peewee and the standard library - a peewee `Model` instance lets you set fields as attributes and has a `.save()`. No third-party packages.
- Keep it small; the worker handles one record at a time.

There's a starter test file at `tests/test_record_sync.py` that builds an in-memory sqlite model so you don't need a real database - please add a couple of focused tests: merging a snapshot updates the fields on the row, and the change is still there when you re-fetch it. Run it with:

    python -m pytest tests/test_record_sync.py -q
