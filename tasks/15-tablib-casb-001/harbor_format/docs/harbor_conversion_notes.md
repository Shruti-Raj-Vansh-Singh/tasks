# Harbor conversion notes - tablib-casb-001

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

- tablib uses a `src/` layout: the package lives at `src/tablib/`. So
  `PYTHONPATH` points at `/workspace/tablib/src` and `REPO_UNDER_TEST` points at
  the repo root `/workspace/tablib`. The oracles add both to `sys.path`.
- tablib has no required runtime dependencies and no `tests/conftest.py`. The
  two oracles and the task's visible tests (`tests/test_sheets.py`) import only
  `tablib` and the standard library, so the verifier image needs only `pytest`.
- The repo's broader suite (`tests/test_tablib.py`) imports optional extras
  (`xlrd`, `odfpy`, `openpyxl`) at module top; it is intentionally NOT collected
  by this task's verifier, which runs only `tests/test_sheets.py`.

## Line endings

All authored scripts and patches are LF. `scripts/normalize_harbor_artifacts.sh`
re-strips CRLF as a safety net; `solve.sh` also runs `tr -d '\r'` on the patch
before applying, so a CRLF checkout on Windows still applies cleanly.
