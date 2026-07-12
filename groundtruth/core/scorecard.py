"""Groundtruth Core — Scorecard & failure taxonomy.

The Groundtruth differentiator: a Detector does not return a boolean. It returns
structured Failure objects that *explain* what went wrong — category, severity,
the causal chain that produced it, and a concrete mitigation. We don't just
measure failure, we explain it. AgentProbe, JudgeKit, and PlannerBench all emit
this same schema.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SEVERITIES = ("low", "medium", "high", "critical")


@dataclass
class Failure:
    case_id: str
    detector: str
    category: str            # e.g. "instruction_hijacking"
    severity: str            # one of SEVERITIES
    summary: str
    chain: list[str] = field(default_factory=list)   # causal steps, human-readable
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Scorecard:
    subject: str
    suite: str
    n_cases: int
    failures: list[Failure] = field(default_factory=list)

    @property
    def failed_cases(self) -> set[str]:
        return {f.case_id for f in self.failures}

    @property
    def robustness(self) -> float:
        """Fraction of cases with no detected failure. 1.0 == clean."""
        if self.n_cases == 0:
            return 1.0
        return round(1 - len(self.failed_cases) / self.n_cases, 4)

    def _counts(self, attr: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for f in self.failures:
            key = getattr(f, attr)
            out[key] = out.get(key, 0) + 1
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "suite": self.suite,
            "n_cases": self.n_cases,
            "robustness_score": self.robustness,
            "n_failures": len(self.failures),
            "by_severity": self._counts("severity"),
            "by_category": self._counts("category"),
            "failures": [f.to_dict() for f in self.failures],
        }
