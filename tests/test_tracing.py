"""Trace shape for a full Qwen case and for the timeout path."""

import pytest

pytestmark = pytest.mark.live


def test_deny_trace_has_four_spans_and_token_totals(corpus_runs):
    case = corpus_runs["app-deny"]

    assert [span["agent"] for span in case.trace] == [
        "intake",
        "enrichment",
        "risk scoring",
        "recommendation",
    ]
    total = 0
    summed = 0
    for span in case.trace:
        assert "input" in span and "output" in span
        assert span["duration_ms"] > 0
        assert span["wall_time_ms"] >= 0
        usage = span["token_usage"]
        assert usage["prompt"] > 0
        assert usage["completion"] > 0
        assert usage["total"] == usage["prompt"] + usage["completion"]
        total += usage["total"]
        summed += usage["prompt"] + usage["completion"]
    assert total == summed
    assert case.decision["decision"] == "deny"


def test_recovered_retry_and_timeout_traces(corpus_runs):
    recovered = corpus_runs["retry"]
    risk_span = next(span for span in recovered.trace if span["agent"] == "risk scoring")
    assert risk_span["attempts"] == 2
    assert risk_span["token_usage"]["total"] > 0

    timed_out = corpus_runs["app-timeout"]
    assert [span["agent"] for span in timed_out.trace] == ["intake", "enrichment", "risk scoring"]
    assert timed_out.trace[2]["token_usage"]["total"] == 0
