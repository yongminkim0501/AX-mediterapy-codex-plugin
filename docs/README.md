# Meditherapy Seeding Review Plugin MVP

This repository contains a Codex plugin MVP that reviews structured Meditherapy influencer seeding plans.

The checker does:

- validate and normalize a canonical JSON plan;
- detect ambiguous and unknown fields;
- evaluate hard constraints with `z3-solver` and tracked rule ids;
- compute soft conflicts as symbol set diffs against an evidence baseline;
- produce marketer-facing Markdown or JSON reports.

The checker does not:

- crawl SNS or creator profiles;
- predict ROAS;
- recommend or rank influencers;
- use an LLM to decide whether a conflict exists;
- implement a full ontology graph.

Public source reference used by the evidence base:

https://blog.featuring.co/case-study-campaign-meditherapy-2026

## Structure

The plugin root is `src/` for submission packaging. Required plugin metadata lives at `src/.codex-plugin/plugin.json`, and the skill entry is `src/skills/meditherapy-seeding-review/SKILL.md`.

## Install Dependency

```bash
python -m pip install -r src/checker/requirements.txt
```

If `z3-solver` is missing, the checker exits with a clear install message.

## CLI Examples

Use `python3` instead of `python` on systems where the `python` command is not installed.

```bash
python src/checker/check_plan.py --plan src/examples/soft_conflict_plan.json --output-format markdown
```

```bash
python src/checker/check_plan.py --plan src/examples/hard_conflict_plan.json --output-format json --debug --debug-dir debug_runs/hard_conflict
```

## Debug Output

With `--debug --debug-dir <path>`, the checker writes raw input, schema result, symbol context, hard constraints, solver result, soft diff, status decision, and final report files. Debug output does not change the final result.

## Verification

Install the checker dependency first, then run the edge-case suite:

```bash
python3 -m pip install -r src/checker/requirements.txt
python3 -m pytest tests
```
