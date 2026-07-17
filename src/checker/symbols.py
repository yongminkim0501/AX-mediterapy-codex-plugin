from __future__ import annotations

from typing import Any


SOFT_FIELDS = {
    "market": ("market",),
    "gender": ("target", "gender"),
    "age_group": ("target", "age_group"),
}


def build_symbol_context(schema_result: dict[str, Any]) -> dict[str, Any]:
    plan = schema_result["normalized_plan"]
    soft_symbol_set = {
        name: value
        for name, path in SOFT_FIELDS.items()
        if (value := get_path(plan, path)) is not None
    }

    atomic_symbols = [f"{key}={value}" for key, value in sorted(soft_symbol_set.items())]

    kpis = get_path(plan, ("kpis",)) or []
    for kpi in kpis:
        atomic_symbols.append(f"kpi={str(kpi).lower()}")

    measurement = get_path(plan, ("measurement",)) or {}
    for key, value in sorted(measurement.items()):
        atomic_symbols.append(f"measurement.{key}={value}")

    budget_limit = get_path(plan, ("budget", "limit"))
    planned_cost = get_path(plan, ("planned_cost",))
    if budget_limit is not None:
        atomic_symbols.append(f"budget.limit={budget_limit}")
    if planned_cost is not None:
        atomic_symbols.append(f"planned_cost={planned_cost}")

    composite_symbols = []
    if {"market", "gender", "age_group"}.issubset(soft_symbol_set):
        composite_symbols.append(
            {
                "symbol": "audience_segment="
                f"{soft_symbol_set['market']}:{soft_symbol_set['gender']}:{soft_symbol_set['age_group']}",
                "derived_from": [
                    f"market={soft_symbol_set['market']}",
                    f"gender={soft_symbol_set['gender']}",
                    f"age_group={soft_symbol_set['age_group']}",
                ],
                "note": "Composite-on-demand; not stored as an independent fact.",
            }
        )

    return {
        "atomic_symbols": atomic_symbols,
        "composite_symbols": composite_symbols,
        "soft_symbol_set": soft_symbol_set,
        "ambiguous_fields": schema_result["ambiguous_fields"],
        "unknown_fields": schema_result["unknown_fields"],
    }


def get_path(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current
