"""Each agent, called alone with a hardcoded input. These tests call local Qwen."""

import pytest

from underwriting.corpus import load_enrichment
from underwriting.adapters import OllamaAdapter
from underwriting.steps import enrichment_agent, intake_agent, recommendation_agent, risk_scoring_agent

pytestmark = pytest.mark.live

APP_REFER = {
    "id": "app-refer",
    "applicant_name": "Luis Ortega",
    "age": 35,
    "years_licensed": 10,
    "prior_at_fault_claims": 0,
    "coverage_amount": None,
    "territory_code": "T1",
}

COMPLETE = {
    "case_id": "app-approve",
    "normalized": {
        "applicant_name": "Amina Cole",
        "age": 42,
        "years_licensed": 20,
        "prior_at_fault_claims": 0,
        "coverage_amount": 50000,
        "territory_code": "T1",
    },
    "missing_fields": [],
}


def test_intake_flags_missing_coverage_on_app_refer():
    client = OllamaAdapter()

    result = intake_agent(APP_REFER, client)

    assert result["case_id"] == "app-refer"
    assert "coverage_amount" in result["missing_fields"]
    assert "coverage_amount" not in result["normalized"]
    assert result["normalized"]["age"] == 35
    assert client.calls == ["intake"]
    assert result["llm"]["model"] == "qwen3:8b"
    assert result["llm"]["prompt_tokens"] > 0


def test_enrichment_uses_the_table_for_app_deny():
    client = OllamaAdapter()
    application = {"case_id": "app-deny", "normalized": {}, "missing_fields": []}

    result = enrichment_agent(application, client, load_enrichment())

    assert result["prior_claim_count"] == 3
    assert result["territory_risk_band"] == "high"
    assert result["critical_gap"] is False
    assert client.calls == ["enrichment"]
    assert result["llm"]["model"] == "qwen3:8b"


def test_enrichment_unknown_id_is_a_critical_gap():
    client = OllamaAdapter()
    application = {"case_id": "app-unknown", "normalized": {}, "missing_fields": []}

    result = enrichment_agent(application, client, load_enrichment())

    assert result["critical_gap"] is True
    assert result["prior_claim_count"] is None
    assert "unknown_applicant" in result["gaps"]
    assert client.calls == ["enrichment"]


def test_risk_scoring_returns_qwen_scores_inside_the_policy_bands():
    approve = risk_scoring_agent("app-approve", {"critical_gap": False, "prior_claim_count": 0, "territory_risk_band": "low"}, OllamaAdapter())
    deny = risk_scoring_agent("app-deny", {"critical_gap": False, "prior_claim_count": 3, "territory_risk_band": "high"}, OllamaAdapter())

    assert 0 <= approve["score"] <= 30
    assert 70 <= deny["score"] <= 100


def test_recommendation_applies_thresholds():
    client = OllamaAdapter()
    enrichment = {"critical_gap": False}

    approved = recommendation_agent(COMPLETE, enrichment, {"score": 18}, client)
    denied = recommendation_agent(COMPLETE, enrichment, {"score": 84}, OllamaAdapter())
    missing_coverage = {
        "case_id": "app-refer",
        "normalized": {"age": 35},
        "missing_fields": ["coverage_amount"],
    }
    referred = recommendation_agent(missing_coverage, enrichment, {"score": 18}, OllamaAdapter())
    no_score = recommendation_agent(COMPLETE, enrichment, None, OllamaAdapter())

    assert approved["decision"] == "approve"
    assert "30" in approved["rule"]
    assert denied["decision"] == "deny"
    assert referred["decision"] == "refer"
    assert "coverage" in referred["reason"]
    assert no_score["decision"] == "refer"
    assert no_score["decision"] != "approve"
    assert client.calls == ["recommendation"]
    assert approved["llm"]["model"] == "qwen3:8b"
