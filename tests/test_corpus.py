"""Corpus loader tests."""

from underwriting.corpus import load_applications, load_enrichment, lookup_enrichment


def test_applications_cover_three_decisions_and_one_timeout():
    applications = load_applications()

    assert len(applications) >= 3
    assert len({row["id"] for row in applications}) == len(applications)
    assert {row["golden_decision"] for row in applications} == {"approve", "deny", "refer"}
    assert sum(1 for row in applications if row["risk_timeout"]) == 1
    approve = next(row for row in applications if row["id"] == "app-approve")
    deny = next(row for row in applications if row["id"] == "app-deny")
    refer = next(row for row in applications if row["id"] == "app-refer")
    assert approve["prior_at_fault_claims"] == 0
    assert approve["coverage_amount"] == 50000
    assert deny["prior_at_fault_claims"] == 3
    assert deny["coverage_amount"] == 500000
    assert refer["coverage_amount"] is None


def test_enrichment_table_returns_facts_or_a_critical_gap():
    table = load_enrichment()

    found = lookup_enrichment(table, "app-approve")
    assert found["critical_gap"] is False
    assert found["territory_risk_band"] == "low"
    assert found["prior_claim_count"] == 0
    missing = lookup_enrichment(table, "app-unknown")
    assert missing["critical_gap"] is True
    assert missing["prior_claim_count"] is None
