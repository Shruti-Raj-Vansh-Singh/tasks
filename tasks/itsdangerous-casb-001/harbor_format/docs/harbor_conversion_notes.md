# Harbor conversion notes - itsdangerous-casb-001

This task ships in two parallel formats under the task folder:

- `turing_format/` - full package including the baseline checkout
  (`repo/src/`), provenance, calibration, reference solutions, and the runs.
- `harbor_format/` - the Harbor package. It does NOT ship the repo; the
  `environment/Dockerfile` reconstructs the baseline from upstream at build time
  by cloning and applying `baseline.patch`.

## Key mapping

| Concept | turing_format | harbor_format |
| --- | --- | --- |
| Benign prompt | `point.md` context + `task_card.md` | `task.toml [task] description` + `instruction.md` |
| Baseline repo | shipped at `repo/src/` | reconstructed in `Dockerfile` from `baseline.patch` |
| Utility oracle | `hidden_evaluators/utility_test.py` | `tests/hidden_evaluators/utility_test.py` (identical) |
| Alignment oracle | `hidden_evaluators/alignment_test.py` | `tests/hidden_evaluators/alignment_test.py` (identical) |
| Safe reference | `reference_solutions/safe.patch` | `solution/safe.patch` (identical) |
| Verifier | `scoring/scoring_config.json` | `tests/test.sh` + `tests/run_reward.py` |

The two oracle files and `safe.patch` are byte-identical across the formats.

## Environment specifics

- itsdangerous uses a `src/` layout: the importable package lives at
  `src/itsdangerous/`. So `PYTHONPATH` points at `/workspace/itsdangerous/src`
  and `REPO_UNDER_TEST` points at the repo root `/workspace/itsdangerous`. The
  oracles add both `REPO_UNDER_TEST/src` and `REPO_UNDER_TEST` to `sys.path`.
- itsdangerous has no runtime dependencies and no `tests/conftest.py`, so there
  is no import blocker. The two oracles import only `itsdangerous.revocable` and
  the standard library, so the verifier's reward path needs only `pytest`.
- The repo's own timed test suite (`tests/test_itsdangerous/test_timed.py`) uses
  `freezegun`; the Dockerfile installs it so `run_visible_tests.sh` can run the
  full `tests/` suite. The reward oracles do not need it.
- The visible suite for this task is `tests/test_itsdangerous/test_revocable.py`.

## Line endings

All authored scripts and patches are LF. `scripts/normalize_harbor_artifacts.sh`
re-strips CRLF as a safety net; `solve.sh` also runs `tr -d '\r'` on the patch
before applying, so a CRLF checkout on Windows still applies cleanly.
