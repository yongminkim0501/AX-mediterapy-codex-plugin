from __future__ import annotations

from copy import deepcopy
from typing import Any


CONFIDENCE_THRESHOLD = 0.75
MISSING = object()

ALLOWED_SHAPE = {
    "campaign": {
        "name": "scalar",
        "objective": "scalar",
    },
    "market": "scalar",
    "target": {
        "gender": "scalar",
        "age_group": "scalar",
    },
    "kpis": "array_scalar",
    "measurement": {
        "tracking_link": "scalar",
        "coupon_code": "scalar",
        "purchase_event": "scalar",
    },
    "budget": {
        "limit": "scalar",
        "currency": "scalar",
    },
    "planned_cost": "scalar",
    "is_experiment_plan": "scalar",
    "experiment_hypothesis": "scalar",
}


def validate_and_normalize(plan: dict[str, Any], confidence_threshold: float = CONFIDENCE_THRESHOLD) -> dict[str, Any]:
    ambiguous_fields: list[dict[str, Any]] = []
    unknown_fields: list[str] = []
    schema_errors: list[dict[str, str]] = []

    normalized = _normalize_object(
        value=plan,
        shape=ALLOWED_SHAPE,
        path="",
        ambiguous_fields=ambiguous_fields,
        unknown_fields=unknown_fields,
        schema_errors=schema_errors,
        confidence_threshold=confidence_threshold,
    )

    return {
        "is_valid": not schema_errors,
        "confidence_threshold": confidence_threshold,
        "normalized_plan": normalized if isinstance(normalized, dict) else {},
        "ambiguous_fields": ambiguous_fields,
        "unknown_fields": unknown_fields,
        "schema_errors": schema_errors,
    }


def _normalize_object(
    value: Any,
    shape: dict[str, Any],
    path: str,
    ambiguous_fields: list[dict[str, Any]],
    unknown_fields: list[str],
    schema_errors: list[dict[str, str]],
    confidence_threshold: float,
) -> Any:
    if not isinstance(value, dict):
        schema_errors.append({"path": path or "$", "message": "Expected object."})
        return {}

    out: dict[str, Any] = {}
    for key, raw in value.items():
        child_path = _join(path, key)
        if key not in shape:
            unknown_fields.append(child_path)
            continue

        spec = shape[key]
        if isinstance(spec, dict):
            if _is_confidence_wrapper(raw):
                schema_errors.append({"path": child_path, "message": "Expected object, got confidence wrapper."})
                continue
            child = _normalize_object(
                raw,
                spec,
                child_path,
                ambiguous_fields,
                unknown_fields,
                schema_errors,
                confidence_threshold,
            )
            if child:
                out[key] = child
        elif spec == "array_scalar":
            child = _normalize_array(raw, child_path, ambiguous_fields, schema_errors, confidence_threshold)
            if child is not MISSING:
                out[key] = child
        elif spec == "scalar":
            child = _normalize_scalar(raw, child_path, ambiguous_fields, schema_errors, confidence_threshold)
            if child is not MISSING:
                out[key] = child
        else:
            schema_errors.append({"path": child_path, "message": f"Unsupported schema spec: {spec}"})

    return out


def _normalize_array(
    value: Any,
    path: str,
    ambiguous_fields: list[dict[str, Any]],
    schema_errors: list[dict[str, str]],
    confidence_threshold: float,
) -> Any:
    if not isinstance(value, list):
        schema_errors.append({"path": path, "message": "Expected array."})
        return MISSING

    out = []
    for index, item in enumerate(value):
        normalized = _normalize_scalar(item, f"{path}[{index}]", ambiguous_fields, schema_errors, confidence_threshold)
        if normalized is not MISSING:
            out.append(normalized)
    return out


def _normalize_scalar(
    value: Any,
    path: str,
    ambiguous_fields: list[dict[str, Any]],
    schema_errors: list[dict[str, str]],
    confidence_threshold: float,
) -> Any:
    if _is_confidence_wrapper(value):
        confidence = value.get("confidence")
        if not isinstance(confidence, (int, float)):
            schema_errors.append({"path": path, "message": "Confidence must be numeric."})
            return MISSING
        if confidence < confidence_threshold:
            ambiguous_fields.append(
                {
                    "path": path,
                    "value": deepcopy(value.get("value")),
                    "raw_value": deepcopy(value.get("raw_value")),
                    "confidence": confidence,
                    "threshold": confidence_threshold,
                }
            )
            return MISSING
        return deepcopy(value.get("value"))

    if isinstance(value, dict):
        schema_errors.append({"path": path, "message": "Expected scalar or confidence wrapper."})
        return MISSING

    return deepcopy(value)


def _is_confidence_wrapper(value: Any) -> bool:
    return isinstance(value, dict) and "value" in value and "confidence" in value


def _join(prefix: str, key: str) -> str:
    return f"{prefix}.{key}" if prefix else key
