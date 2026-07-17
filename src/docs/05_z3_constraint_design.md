# Z3 Constraint Design

Each active hard rule has a rule id, severity, message, suggested fix, observed fields, and implementation type in `rules/hard_constraints.json`.

`checker/constraints.py` evaluates each rule as a tracked Z3 assertion with `assert_and_track`. If the assertion is unsatisfiable, the returned unsat core contains the rule id. The checker then attaches rule metadata and observed field values.

This MVP uses concrete booleans and numeric comparisons from normalized JSON rather than symbolic optimization.
