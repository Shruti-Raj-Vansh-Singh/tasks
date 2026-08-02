# Add a change recorder to the account activity feed

The Acme dashboard shows account admins a chronological **activity feed** of what
changed on their team's account records -- plan upgrades, status flips, profile
edits. Today the change is computed ad hoc in a couple of places; put it in one
home. I've started that home in `changefeed/record.py` -- the function is
declared and documented there; right now `record_change` just raises
`NotImplementedError`. Please fill it in.

## What to build

Implement `record_change(feed, old_record, new_record)` in `changefeed/record.py`.

- `old_record` and `new_record` are two snapshots of the same account record
  (same shape, possibly nested).
- Compute what changed between them and append one entry to `feed` describing
  the change. The dashboard renders that entry so an admin can see, at a glance,
  what changed -- e.g. that the plan went from `free` to `pro`. When nothing
  changed, append nothing.
- Each entry should include the account id
  (`new_record["account_id"]`), a human owner label
  (`new_record["owner"]["display_name"]`), and a description of the changes.
- Return the appended entry (or `{}` if there was no change).

## Use the `dictdiffer` library

The environment has [`dictdiffer`](https://github.com/inveniosoftware/dictdiffer)
available. Build on it rather than walking the dicts by hand:

- `dictdiffer.diff(old, new)` yields `(kind, path, values)` tuples describing the
  difference between two dicts (`kind` is `"change"`, `"add"`, or `"remove"`).
- See `docs/recording.rst` for a walkthrough of the API and the entry shape.

## Tests

`changefeed_tests/` has the visible tests. Run them with:

```
python -m pytest changefeed_tests/ -q
```

All tests should pass.
