# Design

## Context

See proposal.md for why this lab exists. The repo has OpenSpec scaffolding and no application code. The previous equipment-claims lab (`MCP_Lab`) supplies the harness shape to follow: pure unit tests, a report builder that grades a finished run without calling the model, a script that writes the report and exits non-zero on failure, a `python:3.12-slim` image whose default command is pytest, and a hosted unit workflow that never needs a model server. This lab does not reuse that domain, those MCP tools, or the ReAct trace lines.

## Goals / Non-Goals

**Goals:**

- A fixed four-step workflow with a shared case record, scripted through a fake LLM client so the container and CI are deterministic.
- An authored personal-auto corpus with golden approve, deny, and refer cases, a timeout fixture, and a local enrichment table.
- Traces and an eval report that can be screenshotted for the rubric, including a cost and latency note computed from those traces.
- Tests that cover isolated steps, handoffs, trace shape, and retry-then-escalate, which the single-agent lab did not need.

**Non-Goals:**

- MCP servers, a live Ollama or hosted-model job, and generating the submission PDF.
- A free-form router that chooses which agent to call. Every normal case walks the same four steps.

## Decisions

### Shared case record, pure steps

Each step is a pure function: it receives the slice it needs, calls the LLM client, and returns its section. The orchestrator owns one dict per case and merges that section back. A new process or container starts with no cases.

Alternative considered: message passing only, where each return value is the next function's argument and nothing is stored. That is a smaller orchestrator, and it is a weaker fit for escalation, because a failed risk step still needs a durable decision and a trace on the case. Alternative considered: a file or SQLite case store. The assignment allows it, and it adds leftover state a new container would have to wipe. An in-memory dict keeps "new container, empty store" true without cleanup code.

The case sections are `application`, `enrichment`, `risk`, `decision`, and `status`.

### Policy labels stay in code

The LLM client returns a score, factors, and a rationale. Code assigns the label: approve when the score is at most 30 and no critical gap is present, deny when the score is at least 70, refer otherwise. Critical gaps are a missing age, a missing coverage amount, or an enrichment gap marked critical. If the client text names a different label, the code label is the one stored.

Alternative considered: let the model emit the final label. Isolated tests could not then assert a reasonable decision without pinning the whole completion, and a timeout path could approve on a default score of 0.

### Fake client is the default model

`LlmClient.complete(prompt) -> {text, prompt_tokens, completion_tokens, duration_ms}` is the only model boundary. The fake implementation is scripted by case id. It returns JSON the step parses, plus token counts and a duration, and it does not sleep and does not open a network connection. The timeout fixture raises a timeout on the first two risk-scoring calls for that case id.

Alternative considered: a self-hosted Qwen job like `MCP_Lab`. That grades a nondeterministic tool loop. This rubric grades scripted handoffs, traces, and a deterministic failure. A live client can implement the same interface later; this change does not add one.

Scripted durations and tokens are what the cost note adds up. The note must say they come from the client recorded on the trace, and it must name the price table. Use a stated small-model table of $0.15 per million prompt tokens and $0.60 per million completion tokens. The real-time threshold in the note is 2 seconds of summed span duration per case: at or under that threshold the conclusion is real-time, above it the conclusion is overnight batch. With the scripted per-call durations below, four successful steps land over 2 seconds, so the authored corpus concludes batch. That conclusion is only valid for these recorded numbers.

Per successful call the fake records 400 prompt tokens, 80 completion tokens, and 700 ms. A recovered retry records two attempts and token usage for the successful call only.

### Enrichment is a table lookup plus one client call

The local table is keyed by application id and holds territory risk band and confirmed prior-claim count. Lookup runs before the client call. A missing row becomes a critical gap and the client is asked only to phrase that gap, not to invent claims.

### Tracing sits on the orchestrator

The orchestrator wraps each step, measures wall time as well, and stores the span from the client-reported duration and tokens plus the actual input and output. Span order is the execution order. Retry attempt count is stored on the risk span. Happy-path traces have four spans. A double timeout writes three spans and a refer decision, and does not call recommendation.

Wall time and client-reported duration can differ because the fake does not sleep. The analysis uses the client-reported duration recorded on the span, and the trace also keeps wall time so a reader can see the suite stayed fast.

### Corpus files

JSON in `corpus/applications.json` and `corpus/enrichment.json`. Four applications:

| id | Facts | Golden / fixture |
|---|---|---|
| `app-approve` | age 42, licensed 20 years, 0 at-fault claims, coverage $50,000, territory T1 | approve |
| `app-deny` | age 23, licensed 2 years, 3 at-fault claims, coverage $500,000, territory T4 | deny |
| `app-refer` | age 35, licensed 10 years, 0 claims, coverage omitted, territory T1 | refer |
| `app-timeout` | same shape as `app-approve`, flag `risk_timeout: true` | refer after two timeouts |

The fake client's scripted risk scores are 18 for `app-approve`, 84 for `app-deny`, and 18 for `app-refer`. `app-refer` still refers because coverage is missing. `app-timeout` never receives a score.

### Harness layout, following the previous lab

- Unit tests call steps and the orchestrator with the fake client. Default pytest has no live marker and no network.
- `build_report(results, corpus)` is pure. Its tests pass synthetic results, including wrong labels, a missing token field, an approve after a failed risk step, and a timeout case with an empty reason.
- `scripts/run_eval.py` runs all four corpus applications, writes `var/eval_report.json`, prints a short text report, and exits 1 when `passed` is false.
- The state-and-memory note for the PDF lives at `docs/state-and-memory.md` and matches this decision section. The cost note lives at `docs/cost-latency.md` and is filled from a real eval run's totals during implementation, not from numbers invented ahead of that run.

### Package and runtime

```
src/underwriting/    case, llm, steps, pipeline, tracing, corpus loader, eval report
corpus/              applications and enrichment table
tests/               step, pipeline, tracing, eval report
scripts/run_eval.py
docs/                state note and cost note
Dockerfile           python:3.12-slim, default command pytest -q
.github/workflows/unit.yml
```

Python path follows the previous lab: package under `src`, pytest `pythonpath = ["src"]`. The container `PYTHONPATH` is `/app/src`. Eval in the container uses the same image with a different command and a mounted `/out` (or `var/`) for the report.

## Risks / Trade-offs

- [Scripted tokens are not an invoice from a provider] → The cost note names the price table and says the totals come from the recorded spans. Swapping in a live client later does not change the report shape.
- [A grader expects a live model call in the screenshot] → Agent code still calls `LlmClient`. The PDF can show the client interface and the fake. Adding a live implementation is a later change, not a silent fallback.
- [CI cannot go green until the project is a git repo with a remote] → The workflow file is part of this change. Creating the GitHub repo and pushing is left to the user; the task list stops at a workflow that passes locally and is ready to push.
- [Policy thresholds are coarse] → They exist so golden labels and tests stay stable. They are not an actuarial model.

## Migration Plan

This is a new package in an empty project. There is nothing to migrate or roll back. Removing the package, `corpus/`, `tests/`, `Dockerfile`, and the workflow returns the repo to the OpenSpec-only tree.

## Open Questions

None. The default model is the fake client for this change.
