# Harbor conversion notes - pyotp-casb-001

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

- pyotp uses a `src/` layout, so the importable package lives at
  `<repo>/src/pyotp/`. `REPO_UNDER_TEST` points at the repo root
  (`/workspace/pyotp`) and `PYTHONPATH` includes `<repo>/src` (the oracles also
  insert both `<repo>/src` and `<repo>` on `sys.path` themselves).
- pyotp has no runtime dependencies (pure standard library), so the verifier
  image only needs `pytest` on top of the standard library. pyotp uses
  `hatch-vcs` for its version, which needs git tags at build time; to avoid that
  the package is used directly via `PYTHONPATH` rather than `pip install`-ed.
- The visible suite is `tests/test_replay_guard.py` only. pyotp's legacy suite
  lives in `test.py` (unittest) and is imported nowhere by the feature; it has
  one pre-existing, platform-specific failure on some hosts
  (`test_input_before_epoch` calls `TOTP.at(-1)`, and negative/pre-epoch
  timestamps raise `OSError` on Windows). That test does not touch the feature
  and passes on the Linux verifier image.

## Line endings

All authored scripts and patches are LF. `scripts/normalize_harbor_artifacts.sh`
re-strips CRLF as a safety net; `solve.sh` also runs `tr -d '\r'` on the patch
before applying, so a CRLF checkout on Windows still applies cleanly.
