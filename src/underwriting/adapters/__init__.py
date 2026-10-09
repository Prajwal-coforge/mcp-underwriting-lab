"""Model adapters. Application code imports the protocol; Ollama is one implementation."""

from underwriting.adapters.base import (
    CompletionRequest,
    CompletionResult,
    LlmTimeoutError,
    ModelAdapter,
    trace_payload,
)
from underwriting.adapters.ollama import OllamaAdapter

__all__ = [
    "CompletionRequest",
    "CompletionResult",
    "LlmTimeoutError",
    "ModelAdapter",
    "OllamaAdapter",
    "trace_payload",
]
