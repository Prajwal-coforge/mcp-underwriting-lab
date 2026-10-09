"""Standalone underwriting steps. Each one calls a model adapter once per invocation."""

from __future__ import annotations

import json

from underwriting.adapters import CompletionRequest, trace_payload
from underwriting.corpus import lookup_enrichment


def _complete(adapter, case_id: str, step: str, user_content: str) -> dict:
    result = adapter.complete(
        CompletionRequest(
            case_id=case_id,
            step=step,
            user_content=user_content,
            temperature=adapter.temperature,
        )
    )
    return trace_payload(result)


def parse_model_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(stripped[start : end + 1])
    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("model JSON was not an object", stripped, 0)
    return parsed

def intake_agent(raw: dict, client) -> dict:
    missing = []
    if raw.get("age") is None:
        missing.append("age")
    if raw.get("coverage_amount") is None:
        missing.append("coverage_amount")
    llm = _complete(client, raw["id"], "intake", "Normalize this application.")
    normalized = {
        "applicant_name": raw.get("applicant_name"),
        "years_licensed": raw.get("years_licensed"),
        "prior_at_fault_claims": raw.get("prior_at_fault_claims"),
        "territory_code": raw.get("territory_code"),
    }
    if raw.get("age") is not None:
        normalized["age"] = raw["age"]
    if raw.get("coverage_amount") is not None:
        normalized["coverage_amount"] = raw["coverage_amount"]
    return {
        "case_id": raw["id"],
        "normalized": normalized,
        "missing_fields": missing,
        "llm": llm,
    }


def enrichment_agent(application: dict, client, table: dict) -> dict:
    case_id = application["case_id"]
    row = lookup_enrichment(table, case_id)
    if row["critical_gap"]:
        llm = _complete(client, case_id, "enrichment", "Phrase the critical gap. Do not invent claims.")
        return {
            "case_id": case_id,
            "critical_gap": True,
            "gaps": row["gaps"],
            "territory_risk_band": None,
            "prior_claim_count": None,
            "note": llm["text"],
            "llm": llm,
        }
    llm = _complete(
        client,
        case_id,
        "enrichment",
        (
            f"Interpret territory band {row['territory_risk_band']} "
            f"and confirmed claims {row['prior_claim_count']}. Do not invent claims."
        ),
    )
    return {
        "case_id": case_id,
        "critical_gap": False,
        "gaps": [],
        "territory_risk_band": row["territory_risk_band"],
        "prior_claim_count": row["prior_claim_count"],
        "note": llm["text"],
        "llm": llm,
    }


def risk_scoring_agent(case_id: str, enrichment: dict, client) -> dict:
    claims = enrichment.get("prior_claim_count")
    band = enrichment.get("territory_risk_band")
    llm = _complete(
        client,
        case_id,
        "risk scoring",
        (
            "Return JSON with integer score from 0 to 100, factors as a list of strings, "
            "and rationale as a string. "
            f"Confirmed prior at-fault claims: {claims}. Territory band: {band}. "
            "Use 0 to 30 when claims are 0 and the band is low. "
            "Use 70 to 100 when claims are 3 or more or the band is high."
        ),
    )
    parsed = parse_model_json(llm["text"])
    factors = parsed.get("factors") or []
    if not isinstance(factors, list):
        factors = [str(factors)]
    return {
        "score": int(float(parsed["score"])),
        "factors": factors,
        "rationale": str(parsed.get("rationale") or ""),
        "llm": llm,
    }


def critical_gaps(application: dict | None, enrichment: dict | None) -> list[str]:
    gaps = []
    missing = set((application or {}).get("missing_fields") or [])
    normalized = (application or {}).get("normalized") or {}
    if "age" in missing or normalized.get("age") is None:
        gaps.append("age")
    if "coverage_amount" in missing or "coverage_amount" not in normalized:
        gaps.append("coverage_amount")
    if enrichment and enrichment.get("critical_gap"):
        gaps.append("enrichment")
    return gaps


def apply_policy(application: dict | None, enrichment: dict | None, risk: dict | None) -> tuple[str, str]:
    if risk is None or risk.get("score") is None:
        return "refer", "risk score unavailable"
    score = risk["score"]
    if score >= 70:
        return "deny", "score at least 70"
    gaps = critical_gaps(application, enrichment)
    if score <= 30 and not gaps:
        return "approve", "score at most 30 and no critical gap"
    if "coverage_amount" in gaps:
        return "refer", "missing coverage amount"
    if "age" in gaps:
        return "refer", "missing age"
    if "enrichment" in gaps:
        return "refer", "critical enrichment gap"
    return "refer", "score between 31 and 69"


def recommendation_agent(application: dict, enrichment: dict | None, risk: dict | None, client) -> dict:
    llm = _complete(
        client,
        application["case_id"],
        "recommendation",
        "Write the rationale. Policy code assigns the label.",
    )
    label, rule = apply_policy(application, enrichment, risk)
    return {
        "decision": label,
        "rule": rule,
        "reason": rule,
        "rationale": llm["text"],
        "llm": llm,
    }
