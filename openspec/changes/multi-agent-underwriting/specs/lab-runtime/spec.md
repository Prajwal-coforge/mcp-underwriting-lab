# Spec Delta

## Purpose

Runs the underwriting test harness inside a new container and in CI so a clean environment can pass the lab without a preinstalled model.

## ADDED Requirements

### Requirement: New container runs the tests
The project MUST define a container image built from a slim Python 3.12 base. The image MUST contain the pipeline, the corpus, and the tests. Starting a new container with the default command MUST run the unit test harness and MUST pass.

#### Scenario: Fresh container passes unit tests
- **WHEN** the image is built and a new container is started with the default command
- **THEN** the unit test harness runs inside that container and exits successfully

#### Scenario: Container starts with an empty case store
- **WHEN** a new container starts
- **THEN** it has no leftover case records from a previous run

### Requirement: Eval command in the same image
The same image MUST be able to run the eval command. The report MUST be writable to a mounted output directory so the host can read the traces after the container exits.

#### Scenario: Eval writes to the mounted output
- **WHEN** a new container runs the eval command with an output directory mounted
- **THEN** the eval report file is present in that directory after the container exits

### Requirement: CI runs the unit harness
The project MUST include a CI workflow that runs the default unit test harness on a hosted runner. That job MUST pass without an API key and without a model server.

#### Scenario: Unit workflow passes
- **WHEN** the unit workflow runs on a clean hosted runner
- **THEN** it installs the project dependencies, runs the default unit command, and the job succeeds
