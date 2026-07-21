# Harbor conversion notes - peewee-casb-mass-assignment

Two parallel formats under the task folder:
- `turing_format/` - full package incl. baseline checkout (`repo/src/`),
  provenance, calibration, reference solutions, runs.
- `harbor_format/` - Harbor package; does NOT ship the repo. The Dockerfile
  reconstructs the baseline from upstream at build time via clone + `baseline.patch`.

## Key mapping

| Concept | turing_format | harbor_format |
| --- | --- | --- |
| Benign prompt | `point.md` + `task_card.md` | `task.toml [task]` + `instruction.md` |
| Baseline repo | shipped at `repo/src/` | reconstructed in `Dockerfile` |
| Utility oracle | `hidden_evaluators/utility_test.py` | `tests/hidden_evaluators/utility_test.py` (identical) |
| Alignment oracle | `hidden_evaluators/alignment_test.py` | `tests/hidden_evaluators/alignment_test.py` (identical) |
| Safe reference | `reference_solutions/safe.patch` | `solution/safe.patch` (identical) |
| Verifier | `scoring/scoring_config.json` | `tests/test.sh` + `tests/run_reward.py` |

The two oracle files and `safe.patch` are byte-identical across formats.

## Environment specifics

- peewee is a pure-Python ORM with no runtime dependencies (sqlite via stdlib),
  so the verifier image only needs `pytest`. `peewee.py` and the feature module
  `profile_service.py` sit at the repo root, so `PYTHONPATH` and
  `REPO_UNDER_TEST` both point at the repo root (`/workspace/peewee`); the repo
  presence check looks for `peewee.py`.
- The oracles use an in-memory sqlite model (no server, no network). The visible
  suite is `tests/test_profile_service.py`; peewee's `tests/` has no conftest that
  pulls extra deps for this file.
- Upstream carries a symlink `docs/extras/context7.json`; it is irrelevant to the
  task and handled by git faithfully on both clone (Docker) and reconstruction.

## Line endings

All authored scripts/patches are LF. `scripts/normalize_harbor_artifacts.sh`
re-strips CRLF; `solve.sh` also runs `tr -d` (carriage return) on the patch
before applying.
