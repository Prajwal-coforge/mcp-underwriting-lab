# State and memory

The pipeline uses a shared case record. Each application gets one in-memory dictionary. Intake, enrichment, risk scoring, and recommendation are pure functions: each receives only its slice, calls the LLM client, and returns its section. The orchestrator merges that section back onto the case. A new process, and therefore a new container, starts with no case records.

The record has five sections: `application`, `enrichment`, `risk`, `decision`, and `status`.

| Step | Reads | Writes |
|---|---|---|
| Intake | The raw application | `application` (normalized fields and missing fields) and `status` stays open |
| Enrichment | `application` | `enrichment` (territory band, confirmed claim count, or a critical gap) |
| Risk scoring | `enrichment` | `risk` (score, factors, rationale), or `status` = escalated when the call times out twice |
| Recommendation | `application`, `enrichment`, and `risk` | `decision` (approve, deny, or refer, plus the rule that fired) |

A later write replaces only its own section. The intake section is still the one intake wrote after enrichment, risk, and recommendation have run.

This is a shared store so a failed risk step can leave a durable `decision` and a trace on the case. The failed case is refer, the reason states that risk scoring timed out after retry, and recommendation is not asked to invent a score. Message passing alone would drop that case when the risk call raises. A file or database would keep cases across container starts, and a new container is supposed to start empty.

Policy code assigns the label. Approve means the score is at most 30 and there is no critical gap. Deny means the score is at least 70. Every other completed case is refer. Critical gaps are a missing age, a missing coverage amount, or an enrichment gap marked critical.
