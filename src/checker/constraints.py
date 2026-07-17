from __future__ import annotations

from typing import Any

from symbols import get_path


class MissingZ3Error(RuntimeError):
    pass


def evaluate_hard_constraints(schema_result: dict[str, Any], rule_config: dict[str, Any]) -> dict[str, Any]:
    try:
        from z3 import And, Bool, BoolVal, Implies, Not, Or, Solver, unsat
    except ImportError as exc:
        raise MissingZ3Error(
            "z3-solver is required. Install it with: python -m pip install -r src/checker/requirements.txt"
        ) from exc

    plan = schema_result["normalized_plan"]
    ambiguous_paths = {field["path"] for field in schema_result.get("ambiguous_fields", [])}
    violations = []
    unsat_core_ids = []
    checks = []

    for rule in rule_config.get("constraints", []):
        rule_id = rule["id"]
        ambiguous_observed_fields = _ambiguous_observed_fields(rule["observed_fields"], ambiguous_paths)
        if ambiguous_observed_fields:
            checks.append(
                {
                    "id": rule_id,
                    "solver_result": "skipped_ambiguous",
                    "unsat_core": [],
                    "evaluation": {
                        "ambiguous_observed_fields": ambiguous_observed_fields,
                        "reason": "Ambiguous fields are not projected as hard symbols.",
                    },
                }
            )
            continue

        expr, evaluation = _rule_expression(rule["type"], plan, BoolVal, And, Or, Not, Implies)

        solver = Solver()
        tracker = Bool(rule_id)
        solver.assert_and_track(expr, tracker)
        result = solver.check()
        core = [str(item) for item in solver.unsat_core()] if result == unsat else []

        check = {
            "id": rule_id,
            "solver_result": str(result),
            "unsat_core": core,
            "evaluation": evaluation,
        }
        checks.append(check)

        if result == unsat:
            unsat_core_ids.extend(core)
            violations.append(
                {
                    "id": rule_id,
                    "severity": rule["severity"],
                    "message": rule["message"],
                    "suggested_fix": rule["suggested_fix"],
                    "observed_fields": rule["observed_fields"],
                    "observed_values": {field: _get_observed_value(plan, field) for field in rule["observed_fields"]},
                    "unsat_core": core,
                }
            )

    return {
        "engine": "z3",
        "used_assert_and_track": True,
        "overall_result": "unsat" if violations else "sat",
        "unsat_core_ids": sorted(set(unsat_core_ids)),
        "violations": violations,
        "checks": checks,
    }


def _rule_expression(rule_type: str, plan: dict[str, Any], BoolVal: Any, And: Any, Or: Any, Not: Any, Implies: Any) -> Any:
    kpis = {str(kpi).lower() for kpi in (get_path(plan, ("kpis",)) or [])}

    if rule_type == "roas_requires_tracking_or_coupon":
        has_roas = "roas" in kpis
        has_tracking = bool(get_path(plan, ("measurement", "tracking_link")))
        has_coupon = bool(get_path(plan, ("measurement", "coupon_code")))
        return (
            Implies(BoolVal(has_roas), Or(BoolVal(has_tracking), BoolVal(has_coupon))),
            {
                "has_roas_kpi": has_roas,
                "has_tracking_link": has_tracking,
                "has_coupon_code": has_coupon,
            },
        )

    if rule_type == "purchase_conversion_requires_purchase_event":
        has_purchase_conversion = "purchase_conversion" in kpis
        has_purchase_event = bool(get_path(plan, ("measurement", "purchase_event")))
        return (
            Implies(BoolVal(has_purchase_conversion), BoolVal(has_purchase_event)),
            {
                "has_purchase_conversion_kpi": has_purchase_conversion,
                "has_purchase_event": has_purchase_event,
            },
        )

    if rule_type == "planned_cost_lte_budget_limit":
        planned_cost = get_path(plan, ("planned_cost",))
        budget_limit = get_path(plan, ("budget", "limit"))
        both_exist = isinstance(planned_cost, (int, float)) and isinstance(budget_limit, (int, float))
        within_budget = (planned_cost <= budget_limit) if both_exist else True
        return (
            Implies(BoolVal(both_exist), BoolVal(within_budget)),
            {
                "planned_cost": planned_cost,
                "budget_limit": budget_limit,
                "both_exist": both_exist,
                "within_budget": within_budget,
            },
        )

    if rule_type == "experiment_requires_hypothesis":
        is_experiment = bool(get_path(plan, ("is_experiment_plan",)))
        hypothesis = get_path(plan, ("experiment_hypothesis",))
        has_hypothesis = isinstance(hypothesis, str) and bool(hypothesis.strip())
        return (
            Implies(BoolVal(is_experiment), BoolVal(has_hypothesis)),
            {
                "is_experiment_plan": is_experiment,
                "has_experiment_hypothesis": has_hypothesis,
            },
        )

    return BoolVal(True), {"ignored_unknown_rule_type": rule_type}


def _get_observed_value(plan: dict[str, Any], dotted_path: str) -> Any:
    value = get_path(plan, tuple(dotted_path.split(".")))
    return "<missing_or_ambiguous>" if value is None else value


def _ambiguous_observed_fields(observed_fields: list[str], ambiguous_paths: set[str]) -> list[str]:
    matched = []
    for observed in observed_fields:
        for ambiguous in ambiguous_paths:
            if ambiguous == observed or ambiguous.startswith(f"{observed}.") or ambiguous.startswith(f"{observed}["):
                matched.append(observed)
                break
    return matched
