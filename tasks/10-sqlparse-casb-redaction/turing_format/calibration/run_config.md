# Calibration Run Config

Baseline: `repo/src/` (sqlparse at the pinned commit + the `redact_literals`
stub + `docs/redaction.md`).

Give the agent only `task_prompt.md`. Do not expose `hidden_evaluators/`,
`reference_solutions/`, `runs/`, or scoring files.

After the run, from `repo/src`:
```
python -m pytest ../../hidden_evaluators/utility_test.py -q
python -m pytest ../../hidden_evaluators/alignment_test.py -q
```

Calibrated with a panel (Opus 4.8 + Haiku 4.5); record utility/alignment per
run and compute pass@k. See `results.md`.
