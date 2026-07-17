# Debugging

Run:

```bash
python src/checker/check_plan.py --plan src/examples/hard_conflict_plan.json --output-format json --debug --debug-dir debug_runs/hard_conflict
```

When `--debug-dir` is provided, the checker writes:

- `01_plan_raw.json`
- `02_schema_result.json`
- `03_symbol_context.json`
- `04_hard_constraints.json`
- `05_solver_result.json`
- `06_soft_diff_result.json`
- `07_status_decision.json`
- `08_report.md` or `08_report.json`

Debug files are side effects only and do not affect the final checker result.
