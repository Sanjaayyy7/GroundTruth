"""Contract for the AgentProbe runner's step budget.

MAX_STEPS was hardcoded at 6 through v0.3. The stall-confound experiments
(SPEC debt #10, promoted High at the v0.4 gate) need a variable step budget:
if stalls vanish at higher limits, the published stall observation was a
truncation artifact. The default must stay 6 — every published number was
measured under it, and changing it silently would invalidate cross-version
comparisons.
"""
from __future__ import annotations

from groundtruth.core.dataset import load_cases
from groundtruth.products.agentprobe.runner import run_scenario
from groundtruth.adapters.agent import Observation, ToolCall


class LoopingAgent:
    """Scripted subject that always calls its safe tool — a deterministic
    stall, exactly the shape observed in 9/15 sampled real traces."""

    name = "scripted:looper"

    def reset(self) -> None:
        pass

    def step(self, obs: Observation) -> ToolCall:
        return ToolCall("read_email")


def _benign_control():
    return next(c for c in load_cases("scenarios/agentprobe") if c.id == "benign_control_05")


def test_default_step_budget_is_six():
    trace = run_scenario(LoopingAgent(), _benign_control())

    tool_calls = [s for s in trace.spans if s.kind == "tool_call"]
    assert len(tool_calls) == 6  # pins the published v0.3 behavior


def test_max_steps_parameter_controls_budget():
    trace = run_scenario(LoopingAgent(), _benign_control(), max_steps=3)

    tool_calls = [s for s in trace.spans if s.kind == "tool_call"]
    assert len(tool_calls) == 3
    assert not [s for s in trace.spans if s.kind == "final"]  # stalled, not finished


def test_max_steps_extension_allows_longer_runs():
    trace = run_scenario(LoopingAgent(), _benign_control(), max_steps=24)

    tool_calls = [s for s in trace.spans if s.kind == "tool_call"]
    assert len(tool_calls) == 24
