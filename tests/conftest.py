"""Shared Qwen runs for the live pipeline tests. The default suite does not request these."""

import pytest

from underwriting.corpus import load_applications, load_enrichment
from underwriting.adapters import CompletionRequest, LlmTimeoutError, OllamaAdapter
from underwriting.pipeline import run_case


class FirstRiskCallTimesOut(OllamaAdapter):
    def __init__(self):
        super().__init__()
        self._risk_calls = 0

    def complete(self, request: CompletionRequest):
        if request.step == "risk scoring":
            self._risk_calls += 1
            if self._risk_calls == 1:
                self.calls.append(request.step)
                raise LlmTimeoutError("risk scoring timed out")
        return super().complete(request)


def _app(case_id: str) -> dict:
    return next(row for row in load_applications() if row["id"] == case_id)


@pytest.fixture(scope="session")
def corpus_runs():
    table = load_enrichment()
    ran = {
        case_id: run_case(_app(case_id), OllamaAdapter(), table)
        for case_id in ("app-approve", "app-deny", "app-refer", "app-timeout")
    }
    retry_client = FirstRiskCallTimesOut()
    ran["retry"] = run_case(_app("app-approve"), retry_client, table)
    ran["retry_client"] = retry_client
    return ran
