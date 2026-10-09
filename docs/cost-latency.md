# Cost and latency

Figures below are the measured span durations and token counts from a live eval of local Ollama `qwen3:8b` (`var/eval_report.json`). Each successful step called that model with temperature 0. The timeout fixture raises before the risk call, so `app-timeout` is not in this table.

Ollama does not return a dollar invoice. Cost applies this price table to the measured token counts:

- $0.15 per million prompt tokens
- $0.60 per million completion tokens

- app-approve latency_ms=17423 cost=$0.000278
- app-deny latency_ms=16044 cost=$0.000259
- app-refer latency_ms=15367 cost=$0.000246

`app-approve` used 222 prompt tokens and 408 completion tokens: `222 * 0.15 / 1_000_000 + 408 * 0.60 / 1_000_000 = $0.000278`. `app-deny` used 222 prompt and 376 completion tokens ($0.000259). `app-refer` used 222 prompt and 354 completion tokens ($0.000246).

The real-time threshold is 2 seconds (2000 ms) of summed span duration per case. Measured latency is 17423 ms, 16044 ms, and 15367 ms. Each of those is above 2000 ms, so the conclusion is overnight batch. A person waiting on the decision would sit through about 15 to 17 seconds. An overnight batch has room for that latency and for the one retry the risk step is allowed.
