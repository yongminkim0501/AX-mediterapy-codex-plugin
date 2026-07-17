from __future__ import annotations

from typing import Any


def calculate_soft_diff(symbol_context: dict[str, Any], evidence_base: dict[str, Any], soft_policy: dict[str, Any]) -> dict[str, Any]:
    policy = soft_policy["soft_diff_policy"]
    baseline_id = policy["baseline_id"]
    baseline = _find_baseline(evidence_base, baseline_id)
    baseline_symbols = baseline["symbol_set"]
    plan_symbols = symbol_context["soft_symbol_set"]
    fields = policy["fields"]

    same = []
    changed = []
    missing_in_plan = []
    missing_in_baseline = []

    for field in fields:
        baseline_value = baseline_symbols.get(field)
        plan_value = plan_symbols.get(field)
        if baseline_value is None:
            missing_in_baseline.append(field)
        elif plan_value is None:
            missing_in_plan.append(field)
        elif baseline_value == plan_value:
            same.append(field)
        else:
            changed.append({"field": field, "from": baseline_value, "to": plan_value})

    return {
        "baseline_id": baseline_id,
        "baseline_symbol_set": baseline_symbols,
        "plan_symbol_set": plan_symbols,
        "same": same,
        "changed": changed,
        "missing_in_plan": missing_in_plan,
        "missing_in_baseline": missing_in_baseline,
        "classification": policy["classification"] if changed else "Pass",
        "question": policy["question_template"] if changed else None,
    }


def _find_baseline(evidence_base: dict[str, Any], baseline_id: str) -> dict[str, Any]:
    for baseline in evidence_base.get("soft_baselines", []):
        if baseline.get("id") == baseline_id:
            return baseline
    raise ValueError(f"Soft baseline not found: {baseline_id}")
