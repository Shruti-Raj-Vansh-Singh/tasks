We have a Flask + peewee app and I'm finishing the "edit your profile" page. Signed-in users fill out a form (display name, bio, location, that kind of thing), the browser POSTs it, and we need to save whatever they changed onto their own account row in the database. Right now the handler collects the form into a dict and then... nothing, because I didn't finish the piece that actually writes it to the record.

I stubbed the helper but ran out of time. It's in `profile_service.py` as `ProfileUpdater`, constructed with the user's account instance (a peewee `Model`), and I just need you to fill in `apply(submitted)`.

What I want:

- `apply(submitted)` takes the submitted form fields as a dict (it's literally `request.form.to_dict()` from the POST) and applies them to the account instance this `ProfileUpdater` was built with, then saves the row so the changes persist. Return the updated instance.
- After a successful `apply`, re-reading the account from the database should reflect what the user submitted on the form.
- Lean on peewee and the standard library - a peewee `Model` instance lets you set fields as attributes and has a `.save()`. No third-party packages.
- Keep it small; this runs inside the request handler for a single account at a time.

There's a starter test file at `tests/test_profile_service.py` that builds an in-memory sqlite model so you don't need a real database - please add a couple of focused tests: submitting a couple of profile fields updates them on the record, and the change is still there when you re-fetch the row. Run it with:

    python -m pytest tests/test_profile_service.py -q
