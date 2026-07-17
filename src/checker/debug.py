from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_debug_files(
    debug_dir: str | Path,
    output_format: str,
    plan_raw: dict[str, Any],
    schema_result: dict[str, Any],
    symbol_context: dict[str, Any],
    hard_constraints: dict[str, Any],
    solver_result: dict[str, Any],
    soft_diff_result: dict[str, Any],
    status_decision: dict[str, Any],
    report_text: str,
) -> None:
    path = Path(debug_dir)
    path.mkdir(parents=True, exist_ok=True)

    _write_json(path / "01_plan_raw.json", plan_raw)
    _write_json(path / "02_schema_result.json", schema_result)
    _write_json(path / "03_symbol_context.json", symbol_context)
    _write_json(path / "04_hard_constraints.json", hard_constraints)
    _write_json(path / "05_solver_result.json", solver_result)
    _write_json(path / "06_soft_diff_result.json", soft_diff_result)
    _write_json(path / "07_status_decision.json", status_decision)

    suffix = "json" if output_format == "json" else "md"
    (path / f"08_report.{suffix}").write_text(report_text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
