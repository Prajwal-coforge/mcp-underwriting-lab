# Spec Delta

## Purpose

Records what each pipeline step received and produced, how long it took, and how many tokens it used, then rolls those spans up for a cost and latency conclusion.

## ADDED Requirements

### Requirement: Span per step
Every step that runs MUST append one span to that case's trace. The span MUST name the step, the input it received, the output it produced, the duration in milliseconds, and token usage with prompt, completion, and total counts. Spans MUST stay in execution order.

#### Scenario: Normal case has four spans
- **WHEN** a corpus application completes without a timeout
- **THEN** the trace contains four spans in the order intake, enrichment, risk scoring, recommendation, and each span includes input, output, duration, and token usage

#### Scenario: Escalated timeout omits recommendation
- **WHEN** risk scoring times out twice and the case is referred
- **THEN** the trace contains intake, enrichment, and risk scoring spans, and does not contain a recommendation span

### Requirement: Token totals match the spans
The case token total MUST equal the sum of the span token totals. Duration on a span MUST be zero or greater. A retry MUST be visible on the risk-scoring span as an attempt count of two.

#### Scenario: Summed tokens
- **WHEN** a case trace is rolled up
- **THEN** the reported total tokens equal the sum of each span's total tokens

#### Scenario: Recovered timeout records two attempts
- **WHEN** risk scoring times out once and then succeeds
- **THEN** the risk-scoring span records two attempts and still includes token usage for the successful call

### Requirement: Cost and latency analysis
The system MUST write an analysis from the captured traces of the three non-timeout applications. The analysis MUST state total latency and total cost per case, the price table used, and a conclusion that the measured latency fits a real-time use or an overnight batch use. The conclusion MUST cite the measured totals and a stated latency threshold.

#### Scenario: Analysis uses trace numbers
- **WHEN** the three non-timeout traces have been captured
- **THEN** the analysis reports each case's latency as the sum of its span durations and each case's cost from that case's token totals and the price table

#### Scenario: Conclusion names the threshold
- **WHEN** the analysis states real-time or batch
- **THEN** it names the latency threshold used for that judgment and the measured latency it compared
