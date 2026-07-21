# Harbor conversion notes - pyrate-limiter-casb-001

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

- The importable package lives at the repo root (`pyrate_limiter/`), so
  `PYTHONPATH` and `REPO_UNDER_TEST` both point at the repo root
  (`/workspace/pyrate_limiter`), not a `src/` subdirectory.
- PyrateLimiter's core (InMemoryBucket, Rate, RateItem) has no runtime
  dependencies. The redis / psycopg / filelock backends are optional and are not
  imported unless instantiated, so the verifier image only needs `pytest` on top
  of the standard library. No poetry / PEP 517 build is required; the package is
  used directly via `PYTHONPATH`.
- The visible suite is `tests/test_bounded_limiter.py` only. The upstream
  `tests/` also contains backend suites that import `redis` at module load
  (`tests/demo_bucket_factory.py`); those are intentionally not collected here.

## Line endings

All authored scripts and patches are LF. `scripts/normalize_harbor_artifacts.sh`
re-strips CRLF as a safety net; `solve.sh` also runs `tr -d '\r'` on the patch
before applying, so a CRLF checkout on Windows still applies cleanly.
