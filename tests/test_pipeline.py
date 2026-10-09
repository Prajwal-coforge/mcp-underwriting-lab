"""Orchestrator handoff, retry, and escalation. These tests call local Qwen."""

import pytest

pytestmark = pytest.mark.live


def test_intake_section_reaches_enrichment_and_approves(corpus_runs):
    case = corpus_runs["app-approve"]

    enrichment_input = case.trace[1]["input"]
    assert enrichment_input["normalized"] == case.application["normalized"]
    assert enrichment_input["case_id"] == "app-approve"
    assert case.decision["decision"] == "approve"
    assert case.status == "complete"


def test_retry_then_score_in_the_approve_band_still_approves(corpus_runs):
    case = corpus_runs["retry"]
    client = corpus_runs["retry_client"]

    risk_span = next(span for span in case.trace if span["agent"] == "risk scoring")
    assert risk_span["attempts"] == 2
    assert client.calls.count("risk scoring") == 2
    assert "recommendation" in client.calls
    assert case.decision["decision"] == "approve"
    assert 0 <= case.risk["score"] <= 30


def test_second_timeout_refers_without_calling_recommendation(corpus_runs):
    case = corpus_runs["app-timeout"]

    risk_calls = [span for span in case.trace if span["agent"] == "risk scoring"]
    assert len(risk_calls) == 1
    assert risk_calls[0]["attempts"] == 2
    assert [span["agent"] for span in case.trace] == ["intake", "enrichment", "risk scoring"]
    assert case.decision["decision"] == "refer"
    assert case.decision["reason"] == "risk scoring timed out after retry"
    assert case.status == "escalated"
    assert case.trace[2]["token_usage"]["total"] == 0
