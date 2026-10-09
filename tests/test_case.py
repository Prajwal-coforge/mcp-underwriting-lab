"""Case record tests."""

import copy

from underwriting.case import CaseRecord


def test_later_section_does_not_clobber_intake():
    case = CaseRecord("app-approve")
    case.write_section("application", {"case_id": "app-approve", "normalized": {"age": 42}})
    snapshot = copy.deepcopy(case.application)

    case.write_section("enrichment", {"critical_gap": False, "prior_claim_count": 0})

    assert case.application == snapshot
    assert case.enrichment["prior_claim_count"] == 0
