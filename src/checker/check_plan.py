from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import debug as debug_writer
from constraints import MissingZ3Error, evaluate_hard_constraints
from diff import calculate_soft_diff
from report import build_report, decide_status
from schema import validate_and_normalize
from symbols import build_symbol_context


ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "rules"


def main() -> int:
    parser = argparse.ArgumentParser(description="Review a Meditherapy seeding plan deterministically.")
    parser.add_argument("--plan", required=True, help="Path to canonical plan JSON.")
    parser.add_argument("--output-format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--debug", action="store_true", help="Write debug artifacts when --debug-dir is provided.")
    parser.add_argument("--debug-dir", help="Directory for debug artifacts.")
    parser.add_argument(
        "--trace-layer",
        choices=["schema", "symbols", "constraints", "diff", "report"],
        help="Include or focus trace output for a checker layer.",
    )
    args = parser.parse_args()

    try:
        result = run_checker(
            plan_path=Path(args.plan),
            output_format=args.output_format,
            debug_enabled=args.debug,
            debug_dir=args.debug_dir,
            trace_layer=args.trace_layer,
        )
    except MissingZ3Error as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"checker error: {exc}", file=sys.stderr)
        return 1

    print(result)
    return 0


def run_checker(
    plan_path: Path,
    output_format: str,
    debug_enabled: bool = False,
    debug_dir: str | None = None,
    trace_layer: str | None = None,
) -> str:
    plan_raw = _load_json(plan_path)
    hard_rules = _load_json(RULES_DIR / "hard_constraints.json")
    evidence_base = _load_json(RULES_DIR / "evidence_base.json")
    soft_policy = _load_json(RULES_DIR / "soft_insights.json")
    status_policy = _load_json(RULES_DIR / "status_policy.json")

    schema_result = validate_and_normalize(plan_raw)
    symbol_context = build_symbol_context(schema_result)
    hard_result = evaluate_hard_constraints(schema_result, hard_rules)
    soft_diff_result = calculate_soft_diff(symbol_context, evidence_base, soft_policy)
    status_decision = decide_status(hard_result, soft_diff_result, status_policy, schema_result)
    report_text = build_report(
        schema_result,
        symbol_context,
        hard_result,
        soft_diff_result,
        status_decision,
        output_format,
    )

    if trace_layer:
        report_text = _with_trace(
            report_text,
            output_format,
            trace_layer,
            {
                "schema": schema_result,
                "symbols": symbol_context,
                "constraints": hard_result,
                "diff": soft_diff_result,
                "report": {"status_decision": status_decision},
            },
        )

    if debug_enabled and debug_dir:
        debug_writer.write_debug_files(
            debug_dir=debug_dir,
            output_format=output_format,
            plan_raw=plan_raw,
            schema_result=schema_result,
            symbol_context=symbol_context,
            hard_constraints=hard_rules,
            solver_result=hard_result,
            soft_diff_result=soft_diff_result,
            status_decision=status_decision,
            report_text=report_text,
        )

    return report_text


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _with_trace(report_text: str, output_format: str, trace_layer: str, traces: dict[str, Any]) -> str:
    trace_payload = traces[trace_layer]
    if output_format == "json":
        payload = json.loads(report_text)
        payload["trace"] = {trace_layer: trace_payload}
        return json.dumps(payload, ensure_ascii=False, indent=2)

    return (
        report_text
        + "\n\n## Trace: "
        + trace_layer
        + "\n\n```json\n"
        + json.dumps(trace_payload, ensure_ascii=False, indent=2)
        + "\n```"
    )


if __name__ == "__main__":
    raise SystemExit(main())
