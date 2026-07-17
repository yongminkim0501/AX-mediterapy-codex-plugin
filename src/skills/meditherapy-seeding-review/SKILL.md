# Meditherapy Seeding Review

Use this skill when a user provides a Meditherapy influencer seeding plan and asks for constraint or conflict review.

## Workflow

1. Ask for or locate a structured JSON plan that follows `rules/canonical_schema.json`.
2. Run the deterministic checker:

   ```bash
   python src/checker/check_plan.py --plan <plan.json> --output-format markdown
   ```

3. For diagnosis, add debug output:

   ```bash
   python src/checker/check_plan.py --plan <plan.json> --output-format json --debug --debug-dir debug_runs/<case>
   ```

## Review Policy

- Do not infer hard conflicts with free-form LLM judgment.
- Hard constraints are evaluated from canonical JSON fields and `rules/hard_constraints.json`.
- Z3 constraints must be tracked so violations can be mapped back to rule ids.
- Soft conflicts are symbol set diffs against the evidence baseline, not recommendations.
- Ambiguous fields and unknown fields must be surfaced for clarification.

## Output Interpretation

- `Blocked`: at least one blocked hard constraint violation exists.
- `Revise`: at least one revise hard constraint violation exists and no blocked violation exists.
- `Experiment`: no blocking hard issue exists, but soft baseline symbols changed.
- `Pass`: no hard violation and no soft symbol change.

The checker does not crawl SNS, predict ROAS, recommend influencers, or build a full ontology graph.
