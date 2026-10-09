"""Grade a finished underwriting run. Building the report does not call the LLM client."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from underwriting.corpus import load_applications, load_enrichment
from underwriting.adapters import OllamaAdapter
from underwriting.pipeline import case_to_result, run_case

HAPPY_ORDER = ["intake", "enrichment", "risk scoring", "recommendation"]
TOKEN_KEYS = ("prompt", "completion", "total")


def build_report(results: list[dict], corpus: list[dict]) -> dict[str, Any]:
    by_id = {row["id"]: row for row in corpus}
    failures: list[str] = []
    rows = []
    for result in results:
        meta = by_id[result["id"]]
        expected = meta["golden_decision"]
        predicted = result.get("predicted")
        timeout_case = bool(meta.get("risk_timeout"))
        trace = result.get("trace") or []
        if predicted != expected:
            failures.append(f"{result['id']}: expected {expected}, predicted {predicted}")
        if result.get("risk_failed") and predicted == "approve":
            failures.append(f"{result['id']}: approval followed a failed risk score")
        if timeout_case:
            reason = (result.get("escalation_reason") or "").strip()
            if not reason:
                failures.append(f"{result['id']}: escalation reason is empty")
            if any(span.get("agent") == "recommendation" for span in trace):
                failures.append(f"{result['id']}: recommendation ran after risk scoring failed")
        else:
            agents = [span.get("agent") for span in trace]
            if agents != HAPPY_ORDER:
                failures.append(f"{result['id']}: trace steps out of order")
            for span in trace:
                if span.get("duration_ms") is None:
                    failures.append(f"{result['id']}: trace missing duration")
                usage = span.get("token_usage") or {}
                if any(key not in usage for key in TOKEN_KEYS):
                    failures.append(f"{result['id']}: trace missing token usage")
        prompt_tokens = sum((span.get("token_usage") or {}).get("prompt", 0) for span in trace)
        completion_tokens = sum((span.get("token_usage") or {}).get("completion", 0) for span in trace)
        rows.append(
            {
                "id": result["id"],
                "expected": expected,
                "predicted": predicted,
                "correct": predicted == expected,
                "timeout_case": timeout_case,
                "risk_failed": bool(result.get("risk_failed")),
                "escalation_reason": result.get("escalation_reason") or "",
                "latency_ms": sum(span.get("duration_ms") or 0 for span in trace),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "trace": trace,
            }
        )
    return {
        "passed": not failures,
        "failures": failures,
        "cases": len(rows),
        "rows": rows,
    }


def format_report(report: dict[str, Any]) -> str:
    lines = [
        "Eval harness",
        f"model={report.get('model', 'unspecified')} cases={report['cases']} passed={str(report['passed']).lower()}",
        "",
    ]
    for row in report["rows"]:
        lines.append(
            f"{row['id']} expected={row['expected']} predicted={row['predicted']} "
            f"correct={row['correct']} latency_ms={row['latency_ms']} tokens={row['total_tokens']} "
            f"reason={row['escalation_reason'] or 'none'}"
        )
    if report["failures"]:
        lines.append("")
        lines.append("Failures:")
        lines.extend(f"- {failure}" for failure in report["failures"])
    return "\n".join(lines).rstrip() + "\n"


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")


def execute(report_path: Path, client=None) -> dict[str, Any]:
    applications = load_applications()
    table = load_enrichment()
    client = client or OllamaAdapter()
    results = [case_to_result(run_case(raw, client, table)) for raw in applications]
    report = build_report(results, applications)
    report["model"] = getattr(client, "model_id", "qwen3:8b")
    write_report(report_path, report)
    return report
