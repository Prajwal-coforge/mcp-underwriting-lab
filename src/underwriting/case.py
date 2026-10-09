"""In-memory case record. One dict per application, empty when the process starts."""

from __future__ import annotations

import copy

SECTIONS = ("application", "enrichment", "risk", "decision", "status")


class CaseRecord:
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.application = None
        self.enrichment = None
        self.risk = None
        self.decision = None
        self.status = "open"
        self.trace: list[dict] = []
        self.risk_failed = False

    def write_section(self, name: str, value):
        if name not in SECTIONS:
            raise KeyError(name)
        setattr(self, name, copy.deepcopy(value))
