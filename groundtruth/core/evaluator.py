"""Groundtruth Core — Eval Engine.

A Detector inspects a Trace (with its Case) and yields Failures. `evaluate` runs
a set of detectors over a set of traces and aggregates a Scorecard. This is the
product-agnostic heart of the platform: AgentProbe registers safety detectors,
JudgeKit will register agreement/calibration detectors, PlannerBench will
register step-efficiency/recovery detectors — the engine below does not change.
"""
from __future__ import annotations

from typing import Iterable, Protocol

from .dataset import Case
from .scorecard import Failure, Scorecard
from .trace import Trace


class Detector(Protocol):
    name: str

    def detect(self, case: Case, trace: Trace) -> Iterable[Failure]: ...


def evaluate(
    subject: str,
    suite: str,
    cases: list[Case],
    traces: dict[str, Trace],
    detectors: list[Detector],
) -> Scorecard:
    failures: list[Failure] = []
    for case in cases:
        trace = traces[case.id]
        for detector in detectors:
            failures.extend(detector.detect(case, trace))
    return Scorecard(subject=subject, suite=suite, n_cases=len(cases), failures=failures)
