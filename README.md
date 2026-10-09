# Multi-agent underwriting pipeline

Python 3.12. Four steps share one in-memory case record: intake, enrichment, risk scoring, and recommendation. Agents call a `ModelAdapter`. The current adapter is `OllamaAdapter`, which talks to local Ollama `qwen3:8b`. A different provider implements the same `complete` contract and leaves the agents unchanged.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
ollama serve
.venv/bin/pytest -q
.venv/bin/pytest -m live -q
.venv/bin/python scripts/run_eval.py
```

`pytest -q` skips tests marked `live`, same as the equipment-claims lab. `pytest -m live` calls Qwen. The eval report is written to `var/eval_report.json`. State and memory: `docs/state-and-memory.md`. Cost and latency: `docs/cost-latency.md`.

`app-timeout` still raises a timeout on the first two risk-scoring calls before any HTTP request. That is the simulated failure from the assignment, not a stand-in for the model.

Build a new image and run the offline unit tests inside it. The container cannot reach Ollama on the host, so the image does not run the live tests or the eval:

```bash
docker build -t underwriting-lab .
docker run --rm underwriting-lab
```

The image's default command is `pytest -q`.

The `unit` workflow runs `pytest -q` on a GitHub-hosted runner. The `live` workflow runs on the self-hosted runner where Ollama `qwen3:8b` is installed. It runs the live tests, then `scripts/run_eval.py`.
