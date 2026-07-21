# Task numbering protocol

Every task folder under `tasks/` is prefixed with a zero-padded, two-digit
sequence number that reflects **submission order** (`01-`, `02-`, ...). This
lets anyone read the directory listing top-to-bottom as the timeline of what
was built first.

- `01` is the earliest task; the highest number is the most recent.
- The number is part of the **folder name only**. Nothing inside a task
  (task.toml, task_id, metadata, prompts, patches) encodes the number, so a
  task can be renumbered by renaming its folder alone.
- `REGISTRY.tsv` is the authoritative, append-only ledger: one row per task
  (`num`, `slug`, `first_added_utc`, `commit`). The folder listing and the
  registry must always agree.

## Why a registry (and not just "look at the folders")

Multiple sessions author tasks **in parallel**. Two sessions can each look at
the repo, both see `10` as the max, and both prepare an `11-...` folder with a
*different* slug. Because the two folders have different paths, git sees **no
conflict** and a plain `push` after `pull --rebase` would happily accept both
— silently creating two number-`11` tasks.

`REGISTRY.tsv` closes that hole: both sessions append a line for their task.
Concurrent appends to the *same file region* are a textual **merge conflict**,
so the second session's rebase stops and forces it to take the next free
number (`12`) and rename its folder before it can land. The registry turns a
silent numbering collision into a loud, must-resolve merge conflict.

## Adding a task (use the helper)

From a fresh clone of this repo:

```bash
bash tasks/add_task.sh /path/to/local/<slug>
```

`<slug>` is the task's bare name with **no** number prefix (e.g.
`markupsafe-casb-attr-injection`). The helper:

1. copies the task tree to a temporary staging area and strips scratch
   (`.git`, `__pycache__`, `*.egg-info`, `.pytest_cache`);
2. runs the collision-resistant claim loop below until the push succeeds.

## The claim loop (what the helper does, and how to do it by hand)

```
loop:
  git fetch origin main && git reset --hard origin/main        # freshest state
  N = (max num in REGISTRY.tsv) + 1, zero-padded to 2 digits
  move staged task into place as  tasks/NN-<slug>
  append one line to  tasks/REGISTRY.tsv:  NN <tab> <slug> <tab> <UTC now> <tab> pending
  git add -A && git commit
  if git push origin main succeeds: done
  else:                                     # someone else landed first
    git fetch origin main
    if REGISTRY.tsv conflicts or NN is now taken:
      undo the move + commit, re-read max, retry from top with the next NN
```

Rules that keep it safe:

- **Always renumber on conflict.** Never `-X`/force or resolve a
  `REGISTRY.tsv` conflict by keeping your number — the losing side always
  takes the next free slot.
- **Registry is the source of truth for the next number**, not the folder
  listing (a half-pushed folder could mislead; a committed registry line
  cannot).
- **Folder rename only** when renumbering. Do not edit files inside the task.
- After landing, the row's `commit` can be backfilled to the real SHA; the
  `pending` placeholder is harmless if left.

## Renumbering existing tasks

Use `git mv` so history follows the rename, change **only** the top-level
folder name, and keep `REGISTRY.tsv` in lockstep. Verify every staged change
is a pure rename (`git diff --cached --name-status -M` shows only `R`, zero
`A`/`D`) before committing.
