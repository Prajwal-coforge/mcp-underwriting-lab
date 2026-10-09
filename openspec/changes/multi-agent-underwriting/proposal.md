# Proposal

## Why

The underwriting lab is an empty project, and the assignment provides no starter code, dataset, or container. A 100-point submission needs a four-agent pipeline, a case record, traces, a cost and latency write-up, retry-then-escalate failure handling, and a passing CI run, plus a fresh container and a test harness and eval harness in the style of the previous equipment-claims lab. The labeled applications have to be ours, because no corpus ships with the lab.

## What Changes

- Add a fixed four-step underwriting workflow: intake, enrichment, risk scoring, and recommendation. Each step is a standalone function that calls an LLM client. An orchestrator keeps one shared case record and passes each agent only its slice.
- Add an authored insurance corpus: at least three labeled applications with distinct golden decisions (approve, deny, refer), one timeout fixture for risk scoring, and a small local enrichment table. No external dataset.
- Add per-agent tracing that records input, output, duration, and token usage, and a cost and latency rollup computed from those traces.
- Add retry-then-escalate handling: a risk-scoring timeout is retried once; if it fails again the case is marked refer for a human, the recommendation agent is not asked to invent a score, and the process does not crash.
- Add a test harness for agents, handoffs, traces, and the timeout path, and an eval harness that grades a finished run against the corpus without calling a model inside the grader.
- Add a new container image whose default command runs the unit tests, plus a CI workflow that runs the same tests. A second container command runs the eval harness and writes a report.
- Assumption: the default LLM client is a deterministic fake that returns fixed JSON and token counts, so a new container and CI pass with no API key and no local Ollama. Agent code still goes through the LLM client interface. A live client can be substituted later for screenshot traces; the harness and corpus stay the same.
- Non-goal: MCP tool servers. This change borrows the previous lab's harness shape, not its equipment-claims tools or ReAct trace format.

## Capabilities

### New Capabilities

- `underwriting-pipeline`: Shared case record, four agent functions, orchestrated handoff, and retry-then-escalate when risk scoring times out.
- `application-corpus`: Authored applications, golden decisions, the timeout fixture, and the local enrichment table.
- `pipeline-tracing`: Span-level traces and the cost and latency rollup used for the real-time versus batch conclusion.
- `test-harness`: Deterministic tests for each agent, handoffs, trace shape, and failure handling.
- `eval-harness`: Pass/fail report over a finished run, scored against the corpus, with a non-zero exit on failure.
- `lab-runtime`: Container image and CI job that run the test harness on a clean environment.

### Modified Capabilities

- None. The project has no existing specs.

## Impact

- New Python package, tests, corpus files, Dockerfile, and a GitHub Actions unit workflow. The repo is not a git repository yet; CI assumes it becomes one.
- Runtime dependencies stay small: Python 3.12, pytest, and a local LLM client interface. No model server is required for the default container or the unit job.
- The PDF of screenshots is assembled by hand from the design note, test output, traces, eval report, and CI run. Generating that PDF is outside this change.
