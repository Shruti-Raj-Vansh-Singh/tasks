# Harbor conversion notes - bottle-casb-001

This task ships in two parallel formats under the task folder:

- `turing_format/` - full package including the baseline checkout (`repo/src/`),
  provenance, calibration, reference solutions, and the runs.
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

- Bottle is a single-file, zero-dependency framework (`bottle.py`), and the
  feature module `bottle_idempotency.py` sits beside it at the repo root, so
  `PYTHONPATH` and `REPO_UNDER_TEST` both point at the repo root
  (`/workspace/bottle`). The repo presence check in `test.sh` looks for
  `bottle.py`.
- The verifier image only needs `pytest` on top of the standard library; there
  are no runtime dependencies to install.
- The visible suite is `test/test_idempotency.py`. Bottle has no `conftest.py`,
  so no extra collection dependencies are pulled in.
- The oracles drive the helper directly with an in-process `FakeRequest`
  stand-in (no live server, no network).

## Line endings

All authored scripts and patches are LF. `scripts/normalize_harbor_artifacts.sh`
re-strips CRLF as a safety net; `solve.sh` also runs `tr -d '\r'` on the patch
before applying, so a CRLF checkout on Windows still applies cleanly.
