# Planning Conversation Summary

This document summarizes the planning logic that led to the current Meditherapy influencer seeding review plugin. It is not a transcript and does not replace the required raw logs.

## Starting Point

The competition task is to build a Codex plugin that solves a public, verifiable company problem. The selected company context is Meditherapy, and the selected domain is influencer seeding that can connect to revenue.

The initial business question was not treated as "build an influencer recommendation system." Instead, it was reframed as a decision problem:

```text
When a marketer creates a new influencer seeding plan, how can the system show whether the plan keeps, breaks, or intentionally experiments against prior campaign insight and operational constraints?
```

This framing came from two sources:

```text
1. Public/interview context around AX, repeatable judgment, and decision history
2. Public Meditherapy influencer campaign material emphasizing ROAS, purchase conversion, brand fit, authenticity, and influencer language
```

The plugin therefore focuses on plan review, not campaign execution.

## Core AX Interpretation

The planning conversation separated three ideas:

```text
Prediction:
Estimate which influencer, content, or segment may perform well.

Verification:
Check whether a plan violates explicit constraints.

Decision Asset:
Record the basis, difference, exception, and result of decisions so future planning can reuse them.
```

The MVP intentionally implements only a small verification and review loop. It does not predict ROAS, crawl SNS data, rank influencers, or automate campaign operations.

## Key Design Principle

The central principle is:

```text
Hard conflicts are verified.
Soft conflicts are surfaced as intentional experiment questions.
```

Hard conflicts are explicit execution problems:

```text
ROAS KPI without tracking link or coupon code
Purchase conversion KPI without purchase event tracking
Planned cost above budget limit
Experiment plan without an experiment hypothesis
```

Soft conflicts are differences between an existing baseline and a new plan:

```text
KR female 20s baseline -> JP female 20s plan
KR female 20s baseline -> KR male 20s plan
KR female 20s baseline -> TW male 30s plan
```

Soft conflicts are not treated as failures. They are deterministic symbol differences that should prompt questions such as:

```text
This plan changes market from KR to JP. Is this an intended experiment variable?
```

## Why Z3 Is Used

Z3 is not used to prove marketing success. It is used for a narrow formal core:

```text
Given the current explicit hard constraints and plan facts, are those constraints satisfiable?
```

This matters because AX systems repeat decisions. Small execution errors can compound when repeated. The formal layer is used as downside protection, not upside prediction.

The MVP requires:

```text
assert_and_track for hard constraints
unsat_core output
constraint metadata mapping
observed_values in the final report
suggested_fix for each hard violation
```

This makes hard-blocking decisions explainable rather than black-box.

## Ontology And Symbol Formation

The planning did not assume a full ontology graph exists in the MVP. Instead, the design is ontology-ready.

The intended production interpretation is:

```text
Ontology or decision asset data provides the meaning layer.
The plugin projects relevant fields into symbols.
Z3 checks approved hard constraints.
Soft diff compares supported symbol sets.
```

Symbols are handled with these rules:

```text
Atomic-first:
Keep primitive facts such as market=JP, gender=female, age_group=20s.

Composite-on-demand:
Generate audience_segment=JP:female:20s only when needed.

Derived, not independent:
Composite symbols are derived from components and are not stored as independent truth.
```

This prevents combinatorial explosion from generating every possible combination such as:

```text
JP
female
20s
JP_female
JP_20s
female_20s
JP_female_20s
```

Only useful composites are generated for the current plan review.

## Evidence Base And Plan Structuring

The architecture separates reference-side data from case-side data:

```text
Evidence Base:
What the company already knows or has recorded.

Plan Structuring:
What the marketer is proposing now.
```

Both sides should share a canonical schema. In the MVP, the active supported dimensions are:

```text
market
target.gender
target.age_group
kpis
measurement.tracking_link
measurement.coupon_code
measurement.purchase_event
budget.limit
planned_cost
is_experiment_plan
experiment_hypothesis
```

The MVP evidence baseline is intentionally small:

```text
KR / female / 20s
```

This is used to demonstrate deterministic soft symbol diff.

## Role And Governance Reasoning

The planning explicitly rejected the idea that every LLM-discovered relation should become a rule.

The safer model is:

```text
LLM may extract or suggest candidates.
Rule-based gates control what becomes active.
Z3 only receives approved hard constraints.
```

Roles apply to statements, not to variables. For example, ROAS can appear in different statements with different roles:

```text
ROAS is important.
-> business priority

ROAS is the campaign KPI.
-> plan attribute

ROAS requires tracking link or coupon code.
-> hard constraint
```

Future rule updates should be context-specific:

```text
base rule
market-specific rule
product-specific rule
segment-specific rule
campaign-specific experiment candidate
```

Hard constraints should be slow to change. Soft insights can update more frequently.

## MVP Scope Decisions

Included:

```text
Codex plugin manifest
Codex skill instructions
JSON plan checker
Z3 hard constraint validation
unsat_core reporting
soft baseline diff
ambiguous/unknown field reporting
debug artifacts
scenario response pairs
pytest edge-case coverage
```

Excluded:

```text
SNS crawling
Influencer ranking
ROAS prediction
MCP integration
Full ontology graph
Automatic hard-rule promotion
Campaign execution automation
```

These exclusions are intentional. The MVP demonstrates the review architecture, not a full marketing platform.

## Practical Output Philosophy

The plugin should not say:

```text
This plan will succeed.
This influencer will generate sales.
This soft conflict is wrong.
```

It should say:

```text
This plan violates a hard measurable constraint.
This plan differs from the baseline on market/gender/age.
This difference should be confirmed as an intended experiment variable.
This unsupported field is outside the current schema.
```

This framing avoids turning the tool into a punitive review system. It supports marketers by making assumptions explicit.

## Current Known Gaps

The current MVP does not yet model several important marketing dimensions:

```text
influencer_tier
message_control
content_format
product_category
product_claim
regulatory_review
```

When these appear in scenario inputs, the checker reports them as `unknown_fields`. This is intentional and useful: it identifies where the ontology/canonical schema should expand next.

## Final Planning Position

The final planning position is:

```text
This plugin is a deterministic planning review assistant for Meditherapy influencer seeding.

It uses Z3 to explain hard constraint conflicts and symbol diff to surface soft experiment differences.

It converts prior campaign insight into reusable decision assets without claiming to predict revenue or replace marketer judgment.
```

