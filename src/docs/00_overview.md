# Overview

This MVP reviews structured Meditherapy influencer seeding plans with deterministic rules.

It separates:

- hard constraint violations, evaluated by Z3 with tracked rule ids;
- soft conflicts, calculated as symbol diffs against an evidence baseline;
- ambiguous or unknown fields, reported as clarification needs.

The checker does not crawl SNS, predict ROAS, rank influencers, or use an LLM to decide whether a conflict exists.
