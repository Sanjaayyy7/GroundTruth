"""End-to-end evaluation contract for AgentProbe v0.1.

The success criteria for the whole v0.1 foundation live here:
  1. a vulnerable agent scores strictly worse than a hardened one,
  2. the hardened agent is clean on the current suite,
  3. detectors do not false-positive on the benign control,
  4. the whole pipeline is deterministic (byte-identical re-runs).
"""
from __future__ import annotations

from groundtruth.core.dataset import load_cases
from groundtruth.core.evaluator import evaluate
from groundtruth.demo_agents import HardenedAgent, VulnerableAgent
from groundtruth.products.agentprobe.detectors import InjectionCompliance, UnsafeToolCall
from groundtruth.products.agentprobe.runner import run_scenario

SCENARIOS = "scenarios/agentprobe"
DETECTORS = [UnsafeToolCall(), InjectionCompliance()]


def _score(agent_cls):
    cases = load_cases(SCENARIOS)
    agent = agent_cls()
    traces = {c.id: run_scenario(agent, c) for c in cases}
    return evaluate(agent.name, "agentprobe", cases, traces, DETECTORS)


def test_vulnerable_worse_than_hardened():
    vulnerable = _score(VulnerableAgent)
    hardened = _score(HardenedAgent)
    assert vulnerable.robustness < hardened.robustness
    assert hardened.robustness == 1.0
    assert any(f.severity == "critical" for f in vulnerable.failures)


def test_benign_control_no_false_positive():
    vulnerable = _score(VulnerableAgent)
    assert "benign_control_05" not in vulnerable.failed_cases


def test_failures_are_explanatory():
    vulnerable = _score(VulnerableAgent)
    for f in vulnerable.failures:
        assert f.category and f.chain and f.recommendation


def test_deterministic():
    assert _score(VulnerableAgent).to_dict() == _score(VulnerableAgent).to_dict()
