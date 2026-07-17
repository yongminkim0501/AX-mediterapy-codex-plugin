# Data Contracts

Plans are JSON objects matching `rules/canonical_schema.json`.

Fields may be literal values or confidence wrappers:

```json
{ "value": "JP", "confidence": 0.62, "raw_value": "Japan maybe" }
```

When confidence is below the schema threshold, the normalized value is not projected as a hard symbol. The field is listed in `ambiguous_fields` and surfaced in the report.

Unknown fields are collected as paths and do not participate in constraint solving.
