from __future__ import annotations

import json
from typing import Any


def decide_status(
    hard_result: dict[str, Any],
    soft_diff_result: dict[str, Any],
    status_policy: dict[str, Any],
    schema_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidates = []
    severity_to_status = status_policy["hard_severity_to_status"]

    for violation in hard_result["violations"]:
        candidates.append(
            {
                "status": severity_to_status.get(violation["severity"], "Revise"),
                "reason": violation["id"],
            }
        )

    if soft_diff_result["changed"]:
        candidates.append({"status": status_policy["soft_diff_status"], "reason": "soft_symbol_diff"})

    if schema_result and schema_result["ambiguous_fields"]:
        candidates.append({"status": "Revise", "reason": "ambiguous_fields"})

    if not candidates:
        candidates.append({"status": status_policy["default_status"], "reason": "no_conflicts"})

    precedence = status_policy["precedence"]
    selected = sorted(candidates, key=lambda item: precedence.index(item["status"]))[0]
    return {"status": selected["status"], "selected_reason": selected["reason"], "candidates": candidates}


def build_report(
    schema_result: dict[str, Any],
    symbol_context: dict[str, Any],
    hard_result: dict[str, Any],
    soft_diff_result: dict[str, Any],
    status_decision: dict[str, Any],
    output_format: str,
) -> str:
    payload = {
        "status": status_decision["status"],
        "hard_constraints": hard_result,
        "soft_diff": soft_diff_result,
        "ambiguous_fields": schema_result["ambiguous_fields"],
        "unknown_fields": schema_result["unknown_fields"],
        "symbol_context": symbol_context,
    }

    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return _markdown(payload)


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Meditherapy Seeding Review",
        "",
        f"**Status:** {payload['status']}",
        "",
    ]

    hard_violations = payload["hard_constraints"]["violations"]
    lines.append("## Hard Constraints")
    if hard_violations:
        for violation in hard_violations:
            lines.extend(
                [
                    f"- `{violation['id']}` ({violation['severity']}): {violation['message']}",
                    f"  - Suggested fix: {violation['suggested_fix']}",
                    f"  - Unsat core: {', '.join(violation['unsat_core'])}",
                    f"  - Observed: `{json.dumps(violation['observed_values'], ensure_ascii=False)}`",
                ]
            )
    else:
        lines.append("- No hard constraint violations.")
    lines.append("")

    soft = payload["soft_diff"]
    lines.append("## Soft Conflict Diff")
    if soft["changed"]:
        lines.append(f"- Classification: {soft['classification']}")
        lines.append(f"- Same fields: {', '.join(soft['same']) if soft['same'] else 'none'}")
        changed_text = ", ".join(f"{item['field']} {item['from']}->{item['to']}" for item in soft["changed"])
        lines.append(f"- Changed fields: {changed_text}")
        lines.append(f"- Experiment question: {soft['question']}")
    else:
        lines.append("- No soft baseline changes.")
    lines.append("")

    if payload["ambiguous_fields"]:
        lines.append("## Clarification Needed")
        for field in payload["ambiguous_fields"]:
            lines.append(
                f"- `{field['path']}` confidence {field['confidence']} below threshold {field['threshold']} "
                f"(raw: `{field.get('raw_value')}`)"
            )
        lines.append("")

    if payload["unknown_fields"]:
        lines.append("## Unknown Fields")
        for path in payload["unknown_fields"]:
            lines.append(f"- `{path}`")
        lines.append("")

    lines.append("## Symbol Notes")
    lines.append("- Atomic symbols are projected first.")
    lines.append("- Composite symbols are derived from components and are not independent facts.")
    return "\n".join(lines)
