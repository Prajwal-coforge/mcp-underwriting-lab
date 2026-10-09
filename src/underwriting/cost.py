"""Price table applied to the token counts recorded on each span."""

from __future__ import annotations

from decimal import Decimal

PROMPT_USD_PER_MILLION = Decimal("0.15")
COMPLETION_USD_PER_MILLION = Decimal("0.60")
REALTIME_THRESHOLD_MS = 2000


def case_cost(prompt_tokens: int, completion_tokens: int) -> Decimal:
    prompt = Decimal(prompt_tokens) * PROMPT_USD_PER_MILLION
    completion = Decimal(completion_tokens) * COMPLETION_USD_PER_MILLION
    return (prompt + completion) / Decimal(1_000_000)


def format_cost(amount: Decimal) -> str:
    return f"${format(amount, '.6f')}"
