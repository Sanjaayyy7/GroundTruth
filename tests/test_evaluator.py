"""Contract for the Eval Engine's precondition on its inputs.

`evaluate` scores a case list against a trace map. A case with no trace is a
harness wiring mistake — a runner that crashed, a filtered case list, a caller
scoring one suite's cases against another suite's traces. It must surface as a
typed domain error naming what is missing, not as a bare KeyError.
"""
from __future__ import annotations

import pytest

from groundtruth.core.dataset import Case
from groundtruth.core.evaluator import TraceNotFound, evaluate
from groundtruth.core.trace import Trace


def _case(case_id: str) -> Case:
    return Case(id=case_id, suite="agentprobe", description="", spec={})


def test_case_without_a_trace_raises_an_actionable_typed_error():
    cases = [_case("scored_01"), _case("unrun_02")]
    traces = {"scored_01": Trace(subject="fixture", case_id="scored_01")}

    with pytest.raises(TraceNotFound) as exc:
        evaluate("fixture", "agentprobe", cases, traces, [])

    message = str(exc.value)
    assert "unrun_02" in message  # names the case that was never run
    assert "1" in message  # names how many traces were supplied
    assert "scored_01" in message  # names what was supplied


def test_complete_trace_map_scores_without_raising():
    cases = [_case("scored_01")]
    traces = {"scored_01": Trace(subject="fixture", case_id="scored_01")}

    card = evaluate("fixture", "agentprobe", cases, traces, [])

    assert card.n_cases == 1
