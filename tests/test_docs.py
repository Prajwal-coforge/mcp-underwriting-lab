"""The written notes stay aligned with the case record and the eval report."""

from pathlib import Path

from underwriting.cost import case_cost, format_cost

ROOT = Path(__file__).resolve().parents[1]


def test_state_note_names_the_case_sections():
    text = (ROOT / "docs" / "state-and-memory.md").read_text()

    for name in ("application", "enrichment", "risk", "decision", "status"):
        assert name in text


def test_cost_note_records_the_qwen_run():
    text = (ROOT / "docs" / "cost-latency.md").read_text()

    assert "qwen3:8b" in text
    assert "$0.15" in text
    assert "$0.60" in text
    assert "2 seconds" in text
    assert "2000 ms" in text
    assert "overnight batch" in text
    assert "app-approve latency_ms=17423 cost=$0.000278" in text
    assert "app-deny latency_ms=16044 cost=$0.000259" in text
    assert "app-refer latency_ms=15367 cost=$0.000246" in text
    assert format_cost(case_cost(222, 408)) == "$0.000278"
    assert format_cost(case_cost(222, 376)) == "$0.000259"
    assert format_cost(case_cost(222, 354)) == "$0.000246"
