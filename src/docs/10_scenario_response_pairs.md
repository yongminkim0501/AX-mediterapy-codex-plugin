# Scenario Response Pairs

This document records business-facing usage scenarios and the actual checker responses produced by the current MVP implementation.

Assumption: an internal ontology/decision asset already has a baseline soft insight represented as `KR / female / 20s`. The current MVP schema directly supports `market`, `target.gender`, `target.age_group`, `kpis`, `measurement`, `budget`, `planned_cost`, and experiment fields. Variables such as `influencer_tier`, `message_control`, `content_format`, `product_claim`, and `regulatory_review` are intentionally shown as current schema gaps when used.

Command pattern:

```bash
python3 src/checker/check_plan.py --plan src/scenarios/<scenario>.json --output-format json
```

## 1. KR Formula To JP Market

Scenario:

A marketer keeps the known female 20s segment but moves the campaign from Korea to Japan. ROAS measurement is present through a tracking link.

Input file:

```text
src/scenarios/01_kr_to_jp_market_expansion.json
```

Actual response:

```text
status: Experiment
hard violations: none
soft diff same: gender, age_group
soft diff changed: market KR -> JP
unknown fields: none
```

Interpretation:

The checker treats this as an intentional market expansion question, not a hard failure.

## 2. Female Segment To Male Segment

Scenario:

A marketer keeps Korea and the 20s age group, but changes the segment from female skincare buyers to male skincare buyers. ROAS measurement is present through a coupon code.

Input file:

```text
src/scenarios/02_female_to_male_segment_expansion.json
```

Actual response:

```text
status: Experiment
hard violations: none
soft diff same: market, age_group
soft diff changed: gender female -> male
unknown fields: none
```

Interpretation:

The checker asks whether the gender change is an intended experiment variable.

## 3. Nano/Micro Strategy To Macro Strategy

Scenario:

A marketer changes the influencer strategy from a long-tail nano/micro strategy to one macro influencer. ROAS tracking is present.

Input file:

```text
src/scenarios/03_macro_strategy_currently_unmodeled.json
```

Actual response:

```text
status: Pass
hard violations: none
soft diff changed: none
unknown fields: influencer_tier
```

Interpretation:

The current MVP does not model influencer tier as an active ontology field. It reports the unsupported field but does not classify the strategy change as a soft conflict.

## 4. Creator-Owned Language To Strict Script

Scenario:

A marketer uses a strict brand script instead of creator-owned language while tracking purchase conversion.

Input file:

```text
src/scenarios/04_strict_script_currently_unmodeled.json
```

Actual response:

```text
status: Pass
hard violations: none
soft diff changed: none
unknown fields: message_control
```

Interpretation:

The current MVP does not yet model `message_control`. This is a required ontology/schema expansion if creator-language insight is to be checked deterministically.

## 5. ROAS Without Measurement

Scenario:

A marketer sets ROAS as a KPI but provides neither a tracking link nor a coupon code.

Input file:

```text
src/scenarios/05_roas_without_measurement.json
```

Actual response:

```text
status: Blocked
hard violation: HC_ROAS_MEASUREMENT_REQUIRED
unsat core: HC_ROAS_MEASUREMENT_REQUIRED
soft diff changed: none
unknown fields: none
```

Interpretation:

The checker blocks the plan because ROAS cannot be attributed without a tracking link or coupon code.

## 6. Purchase Conversion Without Purchase Event

Scenario:

A marketer sets purchase conversion as a KPI but does not provide purchase event tracking. A coupon code exists, but purchase event tracking is still false.

Input file:

```text
src/scenarios/06_purchase_conversion_without_event.json
```

Actual response:

```text
status: Blocked
hard violation: HC_PURCHASE_EVENT_REQUIRED
unsat core: HC_PURCHASE_EVENT_REQUIRED
soft diff changed: none
unknown fields: none
```

Interpretation:

The checker blocks the plan because purchase conversion cannot be verified without purchase event measurement.

## 7. Japan Strong Claim Review

Scenario:

A marketer plans a Japan campaign with a strong before-after efficacy claim. ROAS tracking is present.

Input file:

```text
src/scenarios/07_jp_claim_review_currently_unmodeled.json
```

Actual response:

```text
status: Experiment
hard violations: none
soft diff same: gender, age_group
soft diff changed: market KR -> JP
unknown fields: product_claim, regulatory_review
```

Interpretation:

The current MVP detects the market expansion but does not yet enforce country/product-claim regulatory review. `product_claim` and `regulatory_review` are schema gaps.

## 8. Budget Exceeded

Scenario:

A marketer keeps the baseline segment but sets planned cost above the approved budget limit.

Input file:

```text
src/scenarios/08_budget_exceeded.json
```

Actual response:

```text
status: Blocked
hard violation: HC_PLANNED_COST_WITHIN_BUDGET
unsat core: HC_PLANNED_COST_WITHIN_BUDGET
soft diff changed: none
unknown fields: none
```

Interpretation:

The checker blocks the plan because planned cost exceeds the budget limit.

## 9. Same Segment, Different Content Format

Scenario:

A marketer keeps the baseline segment but changes the format from Reels to live commerce. ROAS tracking is present.

Input file:

```text
src/scenarios/09_same_segment_format_change_unmodeled.json
```

Actual response:

```text
status: Pass
hard violations: none
soft diff changed: none
unknown fields: content_format
```

Interpretation:

The current MVP does not yet model content format. It reports `content_format` as unknown and does not classify this as a soft conflict.

## 10. Many Variables Changed

Scenario:

A marketer moves from the baseline KR/female/20s formula to TW/male/30s and also changes product, influencer, content, and message assumptions.

Input file:

```text
src/scenarios/10_many_variable_change.json
```

Actual response:

```text
status: Experiment
hard violations: none
soft diff same: none
soft diff changed: market KR -> TW, gender female -> male, age_group 20s -> 30s
unknown fields: product_category, influencer_tier, content_format, message_control
```

Interpretation:

The current MVP deterministically detects the supported audience-segment changes. Other business dimensions are reported as schema gaps, so they are not yet part of soft conflict scoring.

## Summary

The current MVP correctly supports:

```text
- Hard conflicts for ROAS measurement, purchase event measurement, and budget limit
- Z3 unsat core ids for hard conflicts
- Soft symbol diff across market, gender, and age_group
- Unknown-field reporting for ontology dimensions outside the MVP schema
```

The current MVP does not yet support deterministic checks for:

```text
- influencer_tier
- message_control
- content_format
- product_category
- product_claim
- regulatory_review
```

These unsupported dimensions are the next candidates for canonical schema and evidence baseline expansion.
