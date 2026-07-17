# Soft Conflict Diff

Soft conflict handling is a deterministic symbol set comparison.

The demo baseline is:

```json
{ "market": "KR", "gender": "female", "age_group": "20s" }
```

The JP soft conflict example keeps `gender=female` and `age_group=20s` but changes `market` from `KR` to `JP`. This becomes an `Experiment` unless a hard constraint has higher precedence.
