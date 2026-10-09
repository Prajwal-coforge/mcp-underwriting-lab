"""Load the authored application corpus and the local enrichment table."""

from __future__ import annotations

import json
import os
from pathlib import Path

def corpus_dir() -> Path:
    override = os.environ.get("UNDERWRITING_CORPUS")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "corpus"


def load_applications() -> list[dict]:
    path = corpus_dir() / "applications.json"
    return json.loads(path.read_text())


def load_enrichment() -> dict[str, dict]:
    path = corpus_dir() / "enrichment.json"
    return json.loads(path.read_text())


def lookup_enrichment(table: dict[str, dict], case_id: str) -> dict:
    """Return table facts, or a critical gap when the id is absent. Never invent claims."""
    row = table.get(case_id)
    if row is None:
        return {
            "critical_gap": True,
            "gaps": ["unknown_applicant"],
            "territory_risk_band": None,
            "prior_claim_count": None,
        }
    return {
        "critical_gap": False,
        "gaps": [],
        "territory_risk_band": row["territory_risk_band"],
        "prior_claim_count": row["prior_claim_count"],
    }
