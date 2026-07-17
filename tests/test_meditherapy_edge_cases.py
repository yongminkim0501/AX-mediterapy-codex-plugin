from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHECKER_DIR = ROOT / "src" / "checker"
CHECKER_CLI = CHECKER_DIR / "check_plan.py"
sys.path.insert(0, str(CHECKER_DIR))

from check_plan import run_checker  # noqa: E402


def base_plan(**overrides):
    plan = {
        "campaign": {"name": "MVP edge case", "objective": "seed influencers"},
        "market": "KR",
        "target": {"gender": "female", "age_group": "20s"},
        "kpis": ["roas"],
        "measurement": {
            "tracking_link": True,
            "coupon_code": False,
            "purchase_event": False,
        },
        "budget": {"limit": 100, "currency": "KRW"},
        "planned_cost": 100,
        "is_experiment_plan": False,
        "experiment_hypothesis": "",
    }
    deep_update(plan, overrides)
    return plan


def deep_update(target, updates):
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_update(target[key], value)
        else:
            target[key] = value


def review(plan, tmp_path, *, debug=False, debug_dir=None, trace_layer=None):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    report = run_checker(
        plan_path=plan_path,
        output_format="json",
        debug_enabled=debug,
        debug_dir=str(debug_dir) if debug_dir else None,
        trace_layer=trace_layer,
    )
    return json.loads(report)


def violation_ids(result):
    return {item["id"] for item in result["hard_constraints"]["violations"]}


def test_hard_violation_has_priority_over_soft_experiment(tmp_path):
    result = review(
        base_plan(
            market="JP",
            measurement={"tracking_link": False, "coupon_code": False},
        ),
        tmp_path,
    )

    assert result["status"] == "Blocked"
    assert "HC_ROAS_MEASUREMENT_REQUIRED" in violation_ids(result)
    assert result["soft_diff"]["classification"] == "Experiment"
    assert result["soft_diff"]["changed"] == [{"field": "market", "from": "KR", "to": "JP"}]


def test_multiple_hard_violations_expose_core_ids_and_metadata(tmp_path):
    result = review(
        base_plan(
            kpis=["roas", "purchase_conversion"],
            measurement={"tracking_link": False, "coupon_code": False, "purchase_event": False},
            budget={"limit": 50},
            planned_cost=100,
            is_experiment_plan=True,
            experiment_hypothesis="",
        ),
        tmp_path,
    )

    expected = {
        "HC_ROAS_MEASUREMENT_REQUIRED",
        "HC_PURCHASE_EVENT_REQUIRED",
        "HC_PLANNED_COST_WITHIN_BUDGET",
        "HC_EXPERIMENT_HYPOTHESIS_REQUIRED",
    }
    assert result["status"] == "Blocked"
    assert set(result["hard_constraints"]["unsat_core_ids"]) == expected
    assert violation_ids(result) == expected
    for violation in result["hard_constraints"]["violations"]:
        assert violation["unsat_core"] == [violation["id"]]
        assert set(violation["observed_values"]) == set(violation["observed_fields"])


def test_roas_passes_with_tracking_link_even_without_coupon(tmp_path):
    result = review(base_plan(kpis=["roas"], measurement={"tracking_link": True, "coupon_code": False}), tmp_path)

    assert "HC_ROAS_MEASUREMENT_REQUIRED" not in violation_ids(result)
    roas_check = next(check for check in result["hard_constraints"]["checks"] if check["id"] == "HC_ROAS_MEASUREMENT_REQUIRED")
    assert roas_check["solver_result"] == "sat"


def test_purchase_conversion_requires_purchase_event(tmp_path):
    result = review(
        base_plan(kpis=["purchase_conversion"], measurement={"purchase_event": False}),
        tmp_path,
    )

    assert result["status"] == "Blocked"
    assert "HC_PURCHASE_EVENT_REQUIRED" in violation_ids(result)


@pytest.mark.parametrize(
    ("planned_cost", "expected_budget_violation"),
    [
        (100, False),
        (101, True),
    ],
)
def test_budget_boundary_is_inclusive(tmp_path, planned_cost, expected_budget_violation):
    result = review(base_plan(planned_cost=planned_cost), tmp_path)

    assert ("HC_PLANNED_COST_WITHIN_BUDGET" in violation_ids(result)) is expected_budget_violation
    assert result["status"] == ("Blocked" if expected_budget_violation else "Pass")


@pytest.mark.parametrize("hypothesis", [None, "", "   "])
def test_experiment_plan_requires_non_empty_hypothesis(tmp_path, hypothesis):
    result = review(
        base_plan(
            kpis=[],
            measurement={"tracking_link": False},
            is_experiment_plan=True,
            experiment_hypothesis=hypothesis,
        ),
        tmp_path,
    )

    assert result["status"] == "Revise"
    assert "HC_EXPERIMENT_HYPOTHESIS_REQUIRED" in violation_ids(result)
    violation = result["hard_constraints"]["violations"][0]
    assert violation["severity"] == "revise"


def test_soft_diff_marks_only_market_changed(tmp_path):
    result = review(base_plan(market="JP"), tmp_path)

    assert result["status"] == "Experiment"
    assert result["soft_diff"]["changed"] == [{"field": "market", "from": "KR", "to": "JP"}]
    assert result["soft_diff"]["same"] == ["gender", "age_group"]


def test_identical_baseline_has_no_soft_conflict_and_passes(tmp_path):
    result = review(base_plan(), tmp_path)

    assert result["status"] == "Pass"
    assert result["soft_diff"]["changed"] == []
    assert result["soft_diff"]["classification"] == "Pass"
    assert result["hard_constraints"]["violations"] == []


def test_ambiguous_roas_measurement_is_clarification_not_hard_block(tmp_path):
    result = review(
        base_plan(
            measurement={
                "tracking_link": {
                    "value": True,
                    "raw_value": "probably tagged",
                    "confidence": 0.4,
                },
                "coupon_code": False,
            },
        ),
        tmp_path,
    )

    assert result["status"] == "Revise"
    assert "HC_ROAS_MEASUREMENT_REQUIRED" not in violation_ids(result)
    assert [field["path"] for field in result["ambiguous_fields"]] == ["measurement.tracking_link"]
    assert "measurement.tracking_link=True" not in result["symbol_context"]["atomic_symbols"]


def test_unknown_fields_are_reported_without_crashing(tmp_path):
    result = review(base_plan(creator_count=12), tmp_path)

    assert result["status"] == "Pass"
    assert result["unknown_fields"] == ["creator_count"]


def test_debug_mode_does_not_change_decision_or_results(tmp_path):
    plan = base_plan(market="JP")
    no_debug = review(plan, tmp_path)
    debug_dir = tmp_path / "debug"
    with_debug = review(plan, tmp_path, debug=True, debug_dir=debug_dir)

    assert with_debug["status"] == no_debug["status"]
    assert with_debug["hard_constraints"] == no_debug["hard_constraints"]
    assert with_debug["soft_diff"] == no_debug["soft_diff"]
    assert sorted(path.name for path in debug_dir.iterdir()) == [
        "01_plan_raw.json",
        "02_schema_result.json",
        "03_symbol_context.json",
        "04_hard_constraints.json",
        "05_solver_result.json",
        "06_soft_diff_result.json",
        "07_status_decision.json",
        "08_report.json",
    ]


@pytest.mark.parametrize("trace_layer", ["schema", "symbols", "constraints", "diff", "report"])
def test_trace_layer_does_not_fail(tmp_path, trace_layer):
    result = review(base_plan(), tmp_path, trace_layer=trace_layer)

    assert result["status"] == "Pass"
    assert trace_layer in result["trace"]


def test_malformed_plan_json_returns_clear_cli_error(tmp_path):
    plan_path = tmp_path / "malformed.json"
    plan_path.write_text('{"market": "KR"', encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(CHECKER_CLI), "--plan", str(plan_path), "--output-format", "json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "checker error:" in completed.stderr


def test_composite_symbol_is_on_demand_without_combination_explosion(tmp_path):
    result = review(
        base_plan(
            kpis=["roas", "purchase_conversion"],
            measurement={"tracking_link": True, "coupon_code": True, "purchase_event": True},
        ),
        tmp_path,
    )

    composites = result["symbol_context"]["composite_symbols"]
    assert len(composites) == 1
    assert composites[0]["symbol"] == "audience_segment=KR:female:20s"
    assert composites[0]["derived_from"] == ["market=KR", "gender=female", "age_group=20s"]
