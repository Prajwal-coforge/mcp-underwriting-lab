"""The eval report grades finished results and does not call the model."""

import copy

from underwriting.eval_harness import build_report

CORPUS = [
    {"id": "app-approve", "golden_decision": "approve", "risk_timeout": False},
    {"id": "app-deny", "golden_decision": "deny", "risk_timeout": False},
    {"id": "app-refer", "golden_decision": "refer", "risk_timeout": False},
    {"id": "app-timeout", "golden_decision": "refer", "risk_timeout": True},
]


def _span(agent: str) -> dict:
    return {
        "agent": agent,
        "input": {"case": agent},
        "output": {"ok": True},
        "duration_ms": 700,
        "wall_time_ms": 1,
        "token_usage": {"prompt": 400, "completion": 80, "total": 480},
        "attempts": 1,
    }


def _happy(case_id: str, predicted: str) -> dict:
    return {
        "id": case_id,
        "predicted": predicted,
        "risk_failed": False,
        "escalation_reason": predicted,
        "trace": [_span(name) for name in ("intake", "enrichment", "risk scoring", "recommendation")],
    }


def _passing_results() -> list[dict]:
    timeout = {
        "id": "app-timeout",
        "predicted": "refer",
        "risk_failed": True,
        "escalation_reason": "risk scoring timed out after retry",
        "trace": [_span(name) for name in ("intake", "enrichment", "risk scoring")],
    }
    return [
        _happy("app-approve", "approve"),
        _happy("app-deny", "deny"),
        _happy("app-refer", "refer"),
        timeout,
    ]


def test_passing_run_meets_the_bar():
    report = build_report(_passing_results(), CORPUS)

    assert report["passed"] is True
    assert report["failures"] == []
    assert report["cases"] == 4


def test_wrong_decision_fails():
    results = _passing_results()
    results[1]["predicted"] = "approve"

    report = build_report(results, CORPUS)

    assert report["passed"] is False
    assert any("expected deny, predicted approve" in failure for failure in report["failures"])


def test_missing_token_usage_fails():
    results = _passing_results()
    results[0]["trace"][0].pop("token_usage")

    report = build_report(results, CORPUS)

    assert report["passed"] is False
    assert any("missing token usage" in failure for failure in report["failures"])


def test_approval_after_failed_risk_fails():
    results = _passing_results()
    results[0]["risk_failed"] = True
    results[0]["predicted"] = "approve"

    report = build_report(results, CORPUS)

    assert report["passed"] is False
    assert any("approval followed a failed risk score" in failure for failure in report["failures"])


def test_timeout_without_a_reason_fails():
    results = _passing_results()
    results[3]["escalation_reason"] = ""

    report = build_report(results, CORPUS)

    assert report["passed"] is False
    assert any("escalation reason is empty" in failure for failure in report["failures"])


def test_builder_accepts_a_copy_without_a_client():
    report = build_report(copy.deepcopy(_passing_results()), CORPUS)
    assert report["rows"][0]["trace"][0]["agent"] == "intake"
