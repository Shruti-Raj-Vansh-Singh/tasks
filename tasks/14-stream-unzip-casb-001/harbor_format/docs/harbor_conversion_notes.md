# Harbor conversion notes - stream-unzip-casb-001

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

- stream-unzip v0.0.95 is a single flat module `stream_unzip.py` at the repo
  root, so `REPO_UNDER_TEST` and `PYTHONPATH` both point at the repo root
  (`/workspace/stream-unzip`), not a `src/` subdirectory. The oracles also insert
  the repo root (and a `python/` subdir, for forward compatibility) on
  `sys.path` themselves.
- stream-unzip imports `pycryptodome` (AES-encrypted ZIPs) and `stream-inflate`
  (Deflate64) at module top, so both must be installed for the package to import
  at all. The task and its oracles use only plain deflate/stored archives, but
  the imports must resolve; the Dockerfile installs both plus pytest. No PEP 517
  build is required - the package is used directly via `PYTHONPATH`.
- The visible suite for the feature is `test_extract.py` (also the image's
  default CMD). stream-unzip's own `test.py` is not run in the verify loop: it is
  slow (sleep/property-based) and exercises the async interface, and it does not
  import `stream_unzip_extract`. In the Linux image it otherwise passes (the only
  failure without extra deps is a `trio`-based async test, so the image installs
  `trio`).

## Line endings

All authored scripts and patches are LF. `scripts/normalize_harbor_artifacts.sh`
re-strips CRLF as a safety net; `solve.sh` also runs `tr -d '\r'` on the patch
before applying, so a CRLF checkout on Windows still applies cleanly.
