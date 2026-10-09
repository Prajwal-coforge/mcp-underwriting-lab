"""The timeout case raises before the Ollama adapter opens a connection."""

import pytest

from underwriting.adapters import CompletionRequest, LlmTimeoutError, OllamaAdapter


def test_timeout_case_raises_before_calling_qwen(monkeypatch):
    def fail_urlopen(request, timeout):
        raise AssertionError("timeout fixture must not call Ollama")

    monkeypatch.setattr("underwriting.adapters.ollama.urllib.request.urlopen", fail_urlopen)
    adapter = OllamaAdapter()
    request = CompletionRequest(
        case_id="app-timeout",
        step="risk scoring",
        user_content="Score.",
        temperature=0,
    )

    with pytest.raises(LlmTimeoutError):
        adapter.complete(request)
    with pytest.raises(LlmTimeoutError):
        adapter.complete(request)
