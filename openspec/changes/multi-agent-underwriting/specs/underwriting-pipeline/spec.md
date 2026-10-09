# Spec Delta

## Purpose

Turns a raw insurance application into an approve, deny, or refer decision through four ordered steps that share one case record.

## ADDED Requirements

### Requirement: Shared case record
The pipeline MUST keep one case record per application. Intake, enrichment, risk scoring, and recommendation MUST read only the slice they need and MUST write only their own section. A later step MUST leave earlier sections unchanged.

#### Scenario: Enrichment sees the normalized application
- **WHEN** intake has written a normalized application onto the case record
- **THEN** enrichment reads that normalized application and does not receive unrelated later sections

#### Scenario: Later write preserves intake
- **WHEN** enrichment, risk scoring, or recommendation writes its section
- **THEN** the intake section already stored on the case remains unchanged

### Requirement: Four standalone steps
The system MUST expose intake, enrichment, risk scoring, and recommendation as separately callable steps. Each step MUST perform its reasoning through an LLM client call and MUST return a structured result for a known input without requiring the other steps to run.

#### Scenario: Intake normalizes a raw application
- **WHEN** intake is called with a raw application from the corpus
- **THEN** it returns a normalized application that includes the applicant facts it could read and the list of missing fields

#### Scenario: Each step calls the LLM client
- **WHEN** any one of the four steps runs
- **THEN** that step invokes the LLM client exactly once on the success path and includes the client output in its result

### Requirement: Fixed workflow order
The orchestrator MUST run a normal case in this order: intake, then enrichment, then risk scoring, then recommendation. The recommendation label MUST be produced by policy rules on the risk score and data gaps: approve when the score is at most 30 and no critical gap is present, deny when the score is at least 70, and refer otherwise. Critical gaps are a missing age, a missing coverage amount, or an enrichment gap marked critical.

#### Scenario: Clean low score approves
- **WHEN** a completed case has a risk score of 30 or less and no critical gap
- **THEN** the decision is approve and the rationale names the rule that fired

#### Scenario: High score denies
- **WHEN** a completed case has a risk score of 70 or more
- **THEN** the decision is deny

#### Scenario: Missing coverage refers
- **WHEN** intake records coverage amount as missing
- **THEN** the decision is refer and the reason identifies the missing field

### Requirement: Retry then escalate
When the risk-scoring LLM call raises a timeout, the pipeline MUST retry that call once. If the retry succeeds, the pipeline MUST continue to recommendation. If the retry also times out, the pipeline MUST set the decision to refer with a reason that states risk scoring timed out after retry, MUST NOT call recommendation, and MUST NOT exit with an error.

#### Scenario: Timeout recovers on retry
- **WHEN** the first risk-scoring call times out and the second call returns a score
- **THEN** the pipeline continues and recommendation produces a decision from that score

#### Scenario: Second timeout escalates
- **WHEN** the risk-scoring call times out twice
- **THEN** the case decision is refer, the reason states that risk scoring timed out after retry, recommendation is not called, and the process completes without crashing

#### Scenario: No third attempt
- **WHEN** the risk-scoring call times out twice
- **THEN** the LLM client is invoked at most twice for risk scoring on that case
