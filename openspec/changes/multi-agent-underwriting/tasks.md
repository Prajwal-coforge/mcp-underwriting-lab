# Tasks

## 1. Project skeleton

- [x] 1.1 Add `pyproject.toml`, `requirements.txt`, and `src/underwriting/__init__.py` with pytest `pythonpath = ["src"]` and Python 3.12, and verify `pip install -r requirements.txt` then `pytest -q` exits 0 with no tests collected or an empty suite
- [x] 1.2 Write `docs/state-and-memory.md` describing the shared case record, the slice each step reads and writes, and why an in-memory dict was chosen, and verify the doc names the four sections `application`, `enrichment`, `risk`, and `decision` plus `status`

## 2. Corpus

- [x] 2.1 Add `corpus/applications.json` with `app-approve`, `app-deny`, `app-refer`, and `app-timeout` using the facts and golden labels from design.md, and verify a loader test asserts three distinct golden decisions and exactly one timeout flag
- [x] 2.2 Add `corpus/enrichment.json` keyed by those ids with territory band and confirmed claim count, and verify a loader test returns facts for `app-approve` and a critical gap for an unknown id

## 3. Case record and LLM client

- [x] 3.1 Implement the in-memory case record with section writes that do not clobber earlier sections, and verify a test writes enrichment after intake and still reads the original intake section
- [x] 3.2 Implement `LlmClient` and the fake client scripted by case id (scores 18, 84, and 18; 400 prompt tokens, 80 completion tokens, 700 ms; no network), and verify a test gets that payload for `app-approve` and a timeout on the first two risk calls for `app-timeout`

## 4. Standalone steps

- [x] 4.1 Implement intake against the fake client and verify a hardcoded test on `app-refer` returns a normalized application whose missing fields include coverage amount
- [x] 4.2 Implement enrichment as a table lookup plus one client call and verify a hardcoded test on `app-deny` returns the table's claim count and a test on an unknown id returns a critical gap
- [x] 4.3 Implement risk scoring against the fake client and verify a hardcoded test on `app-approve` returns score 18 and a test on `app-deny` returns score 84
- [x] 4.4 Implement recommendation so code applies the 30/70 thresholds and the client supplies rationale only, and verify tests for score 18 with no gaps (approve), score 84 (deny), missing coverage (refer), and a missing risk section (refer, not approve)

## 5. Pipeline and failure handling

- [x] 5.1 Implement the orchestrator in intake → enrichment → risk scoring → recommendation order, merging each result onto the case, and verify a test on `app-approve` shows enrichment received the intake section and the decision is approve
- [x] 5.2 Add the single retry around risk scoring and verify a test where the first call times out and the second returns score 18 still reaches recommendation and decides approve
- [x] 5.3 Escalate `app-timeout` after the second timeout and verify a test asserts two risk attempts, decision refer, a reason that states risk scoring timed out after retry, recommendation not called, and the caller returns normally

## 6. Tracing

- [x] 6.1 Record one span per step that runs, with step name, input, output, client duration, wall time, and prompt, completion, and total tokens, and verify a test on `app-deny` has four spans in order whose token total equals the sum of the spans
- [x] 6.2 Record retry attempt count on the risk span and omit recommendation after a double timeout, and verify a recovered-retry test shows attempt count 2 and the `app-timeout` trace has exactly the intake, enrichment, and risk spans

## 7. Eval harness

- [x] 7.1 Implement `build_report` so it grades finished results without calling the client, and verify tests pass a fully correct corpus run and fail a wrong deny-as-approve, a span missing tokens, an approve after a failed risk step, and a timeout case with an empty reason
- [x] 7.2 Add `scripts/run_eval.py` to run all four corpus applications, write `var/eval_report.json`, and exit 0 only when `passed` is true, and verify that command exits 0 and the file contains the three traces plus the timeout case
- [x] 7.3 Write `docs/cost-latency.md` from the totals in that report using $0.15 per million prompt tokens and $0.60 per million completion tokens, with a 2 second real-time threshold, and verify the per-case latency and cost figures match the report and the conclusion cites those figures and the threshold

## 8. Container and CI

- [x] 8.1 Add a `python:3.12-slim` Dockerfile whose default command is `pytest -q`, and verify `docker build` then `docker run --rm` exits 0
- [x] 8.2 Verify a second `docker run` of that image executes `scripts/run_eval.py` with a mounted output directory and leaves `eval_report.json` on the host
- [x] 8.3 Add `.github/workflows/unit.yml` that installs dependencies and runs `pytest -q` on a hosted runner with no API key, and verify the workflow file contains that command and a local `pytest -q` exits 0

## 9. Integration

- [x] 9.1 Run `pytest -q` and `python scripts/run_eval.py` in one local session and verify both exit 0
