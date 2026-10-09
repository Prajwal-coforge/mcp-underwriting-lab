# Spec Delta

## Purpose

Grades a finished underwriting run against the corpus and fails the run when a decision, a trace, or an escalation does not meet the lab bar.

## ADDED Requirements

### Requirement: Grade a finished run
The eval harness MUST score an already finished run. Building the pass/fail report MUST NOT call the LLM client. The report MUST include a passed flag, a failure list, per-case expected and predicted decisions, and whether each case's trace is complete.

#### Scenario: Report from synthetic results
- **WHEN** the report builder is given finished results for the corpus cases
- **THEN** it returns a report without invoking the LLM client

#### Scenario: Matching run passes
- **WHEN** every non-timeout case predicts its golden decision and has a complete four-span trace, and the timeout case is refer with a timeout reason and no recommendation span
- **THEN** the report passed flag is true and the failure list is empty

### Requirement: Decision and trace failures
The report MUST fail when a non-timeout case predicts a different label than its golden decision, when a happy-path trace is missing a span field or has the steps out of order, when a case is approve while risk scoring failed, or when the timeout case has no escalation reason.

#### Scenario: Wrong decision fails
- **WHEN** a case expected to deny is predicted approve
- **THEN** the report passed flag is false and a failure names that case, the expected label, and the predicted label

#### Scenario: Silent approval fails
- **WHEN** risk scoring failed and the predicted decision is approve
- **THEN** the report passed flag is false and a failure states that an approval followed a failed risk score

#### Scenario: Incomplete trace fails
- **WHEN** a non-timeout trace is missing token usage or duration on any span
- **THEN** the report passed flag is false and a failure identifies the case and the missing field

#### Scenario: Timeout without a reason fails
- **WHEN** the timeout case decision is refer but the escalation reason is empty
- **THEN** the report passed flag is false

### Requirement: Command exits on the report
A command MUST run the three non-timeout applications and the timeout application through the pipeline, write the report to a file, and exit with status 0 when the report passed and status 1 when it did not.

#### Scenario: Failed report exits 1
- **WHEN** the eval command finishes with a report whose passed flag is false
- **THEN** the process exit status is 1 and the report file exists

#### Scenario: Passed report exits 0
- **WHEN** the eval command finishes with a report whose passed flag is true
- **THEN** the process exit status is 0 and the report file contains the three traces and the timeout case
