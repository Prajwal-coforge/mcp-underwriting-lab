"""Orchestrator. Owns the case record, orders the four steps, and retries risk scoring once."""

from __future__ import annotations

import copy
import time

from underwriting.case import CaseRecord
from underwriting.adapters import LlmTimeoutError
from underwriting.steps import enrichment_agent, intake_agent, recommendation_agent, risk_scoring_agent

TIMEOUT_REASON = "risk scoring timed out after retry"


def _wall_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _usage(llm: dict | None) -> tuple[dict, int]:
    if llm is None:
        return {"prompt": 0, "completion": 0, "total": 0}, 0
    prompt = llm["prompt_tokens"]
    completion = llm["completion_tokens"]
    return {"prompt": prompt, "completion": completion, "total": prompt + completion}, llm["duration_ms"]


def _span(agent: str, received, produced, llm: dict | None, wall_ms: int, attempts: int = 1) -> dict:
    usage, duration_ms = _usage(llm)
    return {
        "agent": agent,
        "input": copy.deepcopy(received),
        "output": copy.deepcopy(produced),
        "duration_ms": duration_ms,
        "wall_time_ms": wall_ms,
        "token_usage": usage,
        "attempts": attempts,
    }


def run_case(raw: dict, client, enrichment_table: dict) -> CaseRecord:
    case = CaseRecord(raw["id"])

    started = time.perf_counter()
    application = intake_agent(raw, client)
    case.write_section("application", application)
    case.trace.append(_span("intake", raw, application, application["llm"], _wall_ms(started)))

    started = time.perf_counter()
    enrichment = enrichment_agent(case.application, client, enrichment_table)
    case.write_section("enrichment", enrichment)
    case.trace.append(
        _span("enrichment", case.application, enrichment, enrichment["llm"], _wall_ms(started))
    )

    attempts = 0
    risk = None
    started = time.perf_counter()
    while attempts < 2:
        attempts += 1
        try:
            risk = risk_scoring_agent(case.case_id, case.enrichment, client)
            break
        except LlmTimeoutError:
            risk = None
    wall = _wall_ms(started)
    if risk is None:
        failed = {"error": "risk scoring timed out", "risk_failed": True}
        case.risk_failed = True
        case.write_section("status", "escalated")
        case.write_section(
            "decision",
            {
                "decision": "refer",
                "rule": TIMEOUT_REASON,
                "reason": TIMEOUT_REASON,
                "rationale": None,
                "llm": None,
            },
        )
        case.trace.append(_span("risk scoring", case.enrichment, failed, None, wall, attempts))
        return case

    case.write_section("risk", risk)
    case.trace.append(_span("risk scoring", case.enrichment, risk, risk["llm"], wall, attempts))

    view = {
        "application": case.application,
        "enrichment": case.enrichment,
        "risk": case.risk,
    }
    started = time.perf_counter()
    decision = recommendation_agent(case.application, case.enrichment, case.risk, client)
    case.write_section("decision", decision)
    case.write_section("status", "complete")
    case.trace.append(_span("recommendation", view, decision, decision["llm"], _wall_ms(started)))
    return case


def case_to_result(case: CaseRecord) -> dict:
    decision = case.decision or {}
    return {
        "id": case.case_id,
        "predicted": decision.get("decision"),
        "risk_failed": case.risk_failed,
        "escalation_reason": decision.get("reason") or "",
        "trace": case.trace,
    }
