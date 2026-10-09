# Spec Delta

## Purpose

Proves each underwriting step, the handoffs between them, the trace shape, and the timeout path with deterministic tests that do not call a live model.

## ADDED Requirements

### Requirement: Isolated step tests
The test harness MUST include a separate test for intake, enrichment, risk scoring, and recommendation. Each test MUST call that step with a hardcoded corpus input and a fake LLM client, and MUST assert a reasonable structured result before any orchestrator runs.

#### Scenario: Four isolated tests pass
- **WHEN** the unit suite runs
- **THEN** each of the four steps has a passing test that uses a hardcoded input and does not invoke the other steps

### Requirement: Handoff tests
The test harness MUST verify that the orchestrator writes each result onto the shared case record and that the next step receives that section. It MUST verify that a missing risk score does not produce an approve decision.

#### Scenario: Intake output reaches enrichment
- **WHEN** the orchestrator runs intake and then enrichment on a corpus application
- **THEN** the enrichment input contains the normalized application written by intake

#### Scenario: Missing score does not approve
- **WHEN** recommendation is given a case whose risk section is absent
- **THEN** the decision is refer and is not approve

### Requirement: Failure-path test
The test harness MUST include a test that forces the risk-scoring client to time out on the corpus timeout application. The test MUST assert one retry, a refer decision, no recommendation call, and a successful process completion.

#### Scenario: Timeout test matches retry-then-escalate
- **WHEN** the failure-path test runs the timeout application
- **THEN** risk scoring is attempted twice, the decision is refer, recommendation is not called, and the test process exits successfully

### Requirement: Default suite stays offline
The default unit run MUST use the fake LLM client only. It MUST pass without an API key and without a local model server.

#### Scenario: Unit run has no live marker requirement
- **WHEN** the default unit command runs
- **THEN** the isolated step tests, handoff tests, trace-shape checks, and failure-path test all run and pass
