#!/usr/bin/env python3
"""Render a self-contained, interactive HTML reference-audit report."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TEMPLATE_MARKER = "/*__REFERENCE_AUDIT_DATA__*/"
TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "assets" / "reference-audit-report-template.html"

CORRECT_STATUSES = {"verified"}
AUTO_FIXED_STATUSES = {
    "minor_fix",
    "minor_format_error",
}


def report_category(status: str) -> str:
    """Map exact verifier statuses to the three user-facing report filters."""
    if status in CORRECT_STATUSES:
        return "correct"
    if status in AUTO_FIXED_STATUSES:
        return "auto_fixed"
    if status == "formatted_only":
        return "unchecked"
    return "blocked"


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def build_report_payload(
    *,
    input_path: str,
    results: Iterable[Any],
    format_consistency: dict[str, Any] | None = None,
    runtime: Any | None = None,
) -> dict[str, Any]:
    """Build display data without sorting; input order is a report invariant."""
    items = []
    counts = {"correct": 0, "auto_fixed": 0, "blocked": 0, "unchecked": 0}
    for raw in results:
        row = dict(_plain(raw))
        category = report_category(str(row.get("status", "")))
        counts[category] += 1
        row["report_category"] = category
        items.append(row)

    if isinstance(runtime, dict):
        runtime_data = dict(runtime)
    elif runtime is not None:
        runtime_data = {
            "mode": getattr(runtime, "mode", ""),
            "elapsed_seconds": round(float(getattr(runtime, "elapsed_seconds", 0.0)), 3),
        }
    else:
        runtime_data = {}

    return {
        "schema": "biomedical-reference-verifier.html-report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": input_path,
        "format_consistency": format_consistency or {},
        "runtime": runtime_data or {},
        "summary": {"total": len(items), **counts},
        "results": items,
    }


def _safe_json_for_script(payload: dict[str, Any]) -> str:
    """Serialize JSON so user-supplied citation text cannot end the script tag."""
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def render_html(payload: dict[str, Any], template_path: Path = TEMPLATE_PATH) -> str:
    template = template_path.read_text(encoding="utf-8")
    if template.count(TEMPLATE_MARKER) != 1:
        raise ValueError(f"HTML template must contain exactly one {TEMPLATE_MARKER} marker")
    assignment = f"window.__REFERENCE_AUDIT_REPORT__={_safe_json_for_script(payload)};"
    return template.replace(TEMPLATE_MARKER, assignment)


def write_html_report(
    output_path: Path,
    *,
    input_path: str,
    results: Iterable[Any],
    format_consistency: dict[str, Any] | None = None,
    runtime: Any | None = None,
    template_path: Path = TEMPLATE_PATH,
) -> Path:
    payload = build_report_payload(
        input_path=input_path,
        results=results,
        format_consistency=format_consistency,
        runtime=runtime,
    )
    output_path.write_text(render_html(payload, template_path), encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a verifier audit JSON as an interactive HTML report.")
    parser.add_argument("audit_json", help="reference-audit.json produced with --keep-process-json")
    parser.add_argument("--output", required=True, help="HTML report output path")
    parser.add_argument("--template", default=str(TEMPLATE_PATH), help="Optional compatible HTML template")
    args = parser.parse_args()

    payload = json.loads(Path(args.audit_json).read_text(encoding="utf-8"))
    report = build_report_payload(
        input_path=str(payload.get("input", "")),
        results=payload.get("results", []),
        format_consistency=payload.get("format_consistency", {}),
        runtime=payload.get("runtime", {}),
    )
    Path(args.output).write_text(render_html(report, Path(args.template)), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
