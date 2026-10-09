"""The model port can be satisfied by any adapter. Ollama names stay in the Ollama adapter."""

import io
import json
from pathlib import Path

from underwriting.adapters import CompletionRequest, CompletionResult, ModelAdapter, OllamaAdapter


class StubAdapter:
    """Proves a second provider can satisfy the same contract without Ollama."""

    provider = "stub"
    model_id = "fixture-model"
    calls: list[str] = []

    def complete(self, request: CompletionRequest) -> CompletionResult:
        self.calls.append(request.step)
        return CompletionResult(
            text="ok",
            prompt_tokens=1,
            completion_tokens=1,
            duration_ms=1,
            provider=self.provider,
            model_id=self.model_id,
        )


def _accepts(adapter: ModelAdapter) -> CompletionResult:
    return adapter.complete(
        CompletionRequest(
            case_id="app-approve",
            step="intake",
            user_content="Normalize.",
            temperature=0,
        )
    )


def test_stub_adapter_satisfies_the_model_port():
    result = _accepts(StubAdapter())

    assert result.provider == "stub"
    assert result.model_id == "fixture-model"
    assert result.text == "ok"


def test_ollama_adapter_reports_its_provider():
    adapter = OllamaAdapter(model_id="qwen3:8b")

    assert adapter.provider == "ollama"
    assert adapter.model_id == "qwen3:8b"


def test_ollama_response_fields_stay_inside_the_adapter():
    root = Path(__file__).resolve().parents[1] / "src" / "underwriting"
    leaked = []
    for path in (root / "steps.py", root / "pipeline.py"):
        text = path.read_text()
        for field in ("prompt_eval_count", "eval_count", "/api/chat"):
            if field in text:
                leaked.append(f"{path.name}:{field}")

    assert leaked == []


def test_ollama_adapter_maps_provider_token_counts(monkeypatch):
    payload = json.dumps(
        {
            "message": {"content": json.dumps({"score": 18})},
            "prompt_eval_count": 120,
            "eval_count": 40,
        }
    ).encode()

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        "underwriting.adapters.ollama.urllib.request.urlopen",
        lambda request, timeout: Response(payload),
    )
    result = OllamaAdapter().complete(
        CompletionRequest(
            case_id="app-approve",
            step="risk scoring",
            user_content="Score.",
            temperature=0,
        )
    )

    assert result.prompt_tokens == 120
    assert result.completion_tokens == 40
    assert result.provider == "ollama"
    assert result.model_id == "qwen3:8b"
