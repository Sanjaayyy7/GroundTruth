"""Groundtruth Core — Eval Engine.

A Detector inspects a Trace (with its Case) and yields Failures. `evaluate` runs
a set of detectors over a set of traces and aggregates a Scorecard. This is the
product-agnostic heart of the platform: AgentProbe registers safety detectors,
JudgeKit will register agreement/calibration detectors, PlannerBench will
register step-efficiency/recovery detectors — the engine below does not change.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from .dataset import Case
from .scorecard import COMPLETION_CONTRACT_KEY, Failure, Scorecard
from .trace import Trace


class TraceNotFound(Exception):
    """A case under evaluation has no trace. CLI maps this to exit code 2."""


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
        try:
            trace = traces[case.id]
        except KeyError:
            supplied = ", ".join(sorted(traces)) or "none"
            raise TraceNotFound(
                f"no trace for case '{case.id}' in suite '{suite}' — "
                f"{len(traces)} trace(s) supplied ({supplied}). Every case "
                f"must be run before it is scored: pass the traces the suite "
                f"runner produced over this exact case list, keyed by case id"
            ) from None
        for detector in detectors:
            failures.extend(detector.detect(case, trace))
    return Scorecard(
        subject=subject,
        suite=suite,
        n_cases=len(cases),
        failures=failures,
        # why: the utility denominator is a property of the case list, so it is
        # established here where the case list is in hand — it cannot be
        # recovered from the failures afterwards.
        completion_eligible=frozenset(
            c.id for c in cases if c.spec.get(COMPLETION_CONTRACT_KEY)
        ),
    )
