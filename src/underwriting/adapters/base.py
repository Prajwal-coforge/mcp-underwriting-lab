"""Model port. Agents depend on this contract, not on a provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LlmTimeoutError(TimeoutError):
    """The model call exceeded its time limit."""


@dataclass(frozen=True)
class CompletionRequest:
    case_id: str
    step: str
    user_content: str
    temperature: float


@dataclass(frozen=True)
class CompletionResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    duration_ms: int
    provider: str
    model_id: str


class ModelAdapter(Protocol):
    provider: str
    model_id: str
    calls: list[str]

    def complete(self, request: CompletionRequest) -> CompletionResult: ...


def raise_if_timeout_case(case_id: str, step: str, seen: dict[str, int]) -> None:
    """app-timeout fails the first two risk calls before any provider work."""
    if step == "risk scoring" and case_id == "app-timeout":
        count = seen.get(case_id, 0) + 1
        seen[case_id] = count
        if count <= 2:
            raise LlmTimeoutError("risk scoring timed out")


def trace_payload(result: CompletionResult) -> dict:
    """Provider-neutral usage stored on the case span."""
    return {
        "text": result.text,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "duration_ms": result.duration_ms,
        "model": result.model_id,
    }
