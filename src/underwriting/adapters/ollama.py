"""Ollama adapter. Provider field names stay in this file."""

from __future__ import annotations

import json
import os
import time
import urllib.request

from underwriting.adapters.base import (
    CompletionRequest,
    CompletionResult,
    LlmTimeoutError,
    raise_if_timeout_case,
)


class OllamaAdapter:
    """Local model through Ollama. Swap this class to change providers."""

    provider = "ollama"

    def __init__(
        self,
        model_id: str | None = None,
        host: str | None = None,
        temperature: float | None = None,
    ):
        self.model_id = model_id or os.environ.get("UNDERWRITING_LLM_MODEL", "qwen3:8b")
        self.host = (host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
        if temperature is None:
            temperature = float(os.environ.get("UNDERWRITING_LLM_TEMPERATURE", "0"))
        self.temperature = temperature
        self.calls: list[str] = []
        self._risk_timeouts: dict[str, int] = {}

    def complete(self, request: CompletionRequest) -> CompletionResult:
        self.calls.append(request.step)
        raise_if_timeout_case(request.case_id, request.step, self._risk_timeouts)
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": request.user_content}],
            "stream": False,
            "think": False,
            "format": "json",
            "keep_alive": "10m",
            "options": {"temperature": request.temperature},
        }
        http_request = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(http_request, timeout=180) as response:
                body = json.load(response)
        except TimeoutError as exc:
            raise LlmTimeoutError("ollama call timed out") from exc
        duration_ms = int((time.perf_counter() - started) * 1000)
        message = body.get("message")
        if not isinstance(message, dict) or "content" not in message:
            raise RuntimeError(f"Ollama returned no message: {body}")
        return CompletionResult(
            text=message["content"],
            prompt_tokens=int(body.get("prompt_eval_count") or 0),
            completion_tokens=int(body.get("eval_count") or 0),
            duration_ms=duration_ms,
            provider=self.provider,
            model_id=self.model_id,
        )
