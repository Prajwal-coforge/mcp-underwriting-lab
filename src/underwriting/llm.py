"""Backward-compatible names for the model adapter."""

from underwriting.adapters.base import LlmTimeoutError
from underwriting.adapters.ollama import OllamaAdapter

__all__ = ["LlmTimeoutError", "OllamaAdapter"]
