# Spec Delta

## Purpose

Provides the authored insurance applications, golden decisions, and local enrichment facts the pipeline and both harnesses run against.

## ADDED Requirements

### Requirement: Authored applications
The corpus MUST be stored with the project and MUST contain at least three personal-auto applications with distinct identifiers. Each application MUST include applicant name, age or an explicit omission, years licensed, prior at-fault claim count, requested coverage amount or an explicit omission, and territory code. The corpus MUST NOT depend on a downloaded or third-party dataset.

#### Scenario: Three applications load from the project
- **WHEN** the corpus is loaded
- **THEN** at least three applications are returned and each has a unique identifier and the fields above

### Requirement: Golden decisions
Each non-timeout application MUST declare one golden decision of approve, deny, or refer. Across those applications the golden decisions MUST include all three labels. The facts on each application MUST be consistent with that label under the pipeline policy rules.

#### Scenario: Labels cover approve, deny, and refer
- **WHEN** the non-timeout applications are listed
- **THEN** their golden decisions include approve, deny, and refer

#### Scenario: Approve case is low risk on the facts
- **WHEN** the application whose golden decision is approve is read
- **THEN** it includes age, coverage amount, zero prior at-fault claims, and a low requested coverage amount

#### Scenario: Deny case is high risk on the facts
- **WHEN** the application whose golden decision is deny is read
- **THEN** it includes multiple prior at-fault claims and a high requested coverage amount

#### Scenario: Refer case omits a critical field
- **WHEN** the application whose golden decision is refer is read
- **THEN** it omits coverage amount or age

### Requirement: Timeout fixture
The corpus MUST include one additional application marked as the risk-scoring timeout case. Its facts MUST otherwise be complete enough to score. The eval and test harnesses MUST be able to select it without changing the other applications.

#### Scenario: Timeout case is addressable
- **WHEN** the corpus is loaded
- **THEN** exactly one application is flagged so that risk scoring times out, and that application is distinct from the three golden-decision applications

### Requirement: Local enrichment table
The corpus MUST include a local table of enrichment facts keyed by application identifier. For each known application the table MUST supply territory risk band and a confirmed prior-claim count. An unknown identifier MUST yield a critical enrichment gap rather than invented facts.

#### Scenario: Known applicant enriches
- **WHEN** enrichment looks up an application identifier present in the table
- **THEN** it receives a territory risk band and a confirmed prior-claim count

#### Scenario: Unknown applicant is a critical gap
- **WHEN** enrichment looks up an identifier that is not in the table
- **THEN** the result is a critical enrichment gap and no fabricated claim count
