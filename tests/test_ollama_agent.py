"""Contract for the Ollama adapter — the first real-LLM subject.

Action parsing is pinned by unit tests with zero network. The live integration
test runs only when a local Ollama server is reachable; it is a smoke check
that a real model can be driven through the protocol, not an assertion about
any model's safety.
"""
from __future__ import annotations

import json
import urllib.request

import pytest

from groundtruth.adapters.agent import Finish, ToolCall
from groundtruth.adapters.ollama_agent import OllamaAgent, parse_action

TOOLS = ["read_email", "transfer_funds"]


def test_parse_tool_action():
    action = parse_action('{"action": "tool", "tool": "read_email"}', TOOLS)

    assert isinstance(action, ToolCall)
    assert action.name == "read_email"


def test_parse_tool_action_with_args():
    action = parse_action(
        '{"action": "tool", "tool": "transfer_funds", "args": {"amount": "100"}}', TOOLS
    )

    assert isinstance(action, ToolCall)
    assert action.args == {"amount": "100"}


def test_parse_finish_action():
    action = parse_action('{"action": "finish", "answer": "All done."}', TOOLS)

    assert isinstance(action, Finish)
    assert action.answer == "All done."


def test_parse_survives_markdown_fences_and_chatter():
    text = 'Sure! Here is my move:\n```json\n{"action": "tool", "tool": "read_email"}\n```'

    action = parse_action(text, TOOLS)

    assert isinstance(action, ToolCall) and action.name == "read_email"


def test_parse_unknown_tool_becomes_finish_with_evidence():
    """A hallucinated tool name must not crash the runner; the raw text stays
    in the trace so detectors and humans can see what the model tried."""
    action = parse_action('{"action": "tool", "tool": "rm_rf_root"}', TOOLS)

    assert isinstance(action, Finish)
    assert "rm_rf_root" in action.answer


def test_parse_tool_named_directly_in_action_field():
    """Observed in the wild (phi4-mini, mistral:7b emit this): the tool name
    lands in the 'action' field itself. Intent is unambiguous, so the adapter
    must translate it — otherwise the harness measures format compliance and
    reports it as over-refusal, a measurement artifact, not safety."""
    action = parse_action('{"action": "read_email", "tool": "", "args": {"q": "x"}}', TOOLS)

    assert isinstance(action, ToolCall)
    assert action.name == "read_email"
    assert action.args == {"q": "x"}


def test_parse_unavailable_tool_in_action_field_still_fails_open():
    action = parse_action('{"action": "rm_rf_root", "args": {}}', TOOLS)

    assert isinstance(action, Finish)


def test_parse_garbage_becomes_finish_preserving_text():
    action = parse_action("I think I should probably read the email first?", TOOLS)

    assert isinstance(action, Finish)
    assert "read the email" in action.answer


def _ollama_up() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _ollama_up(), reason="local Ollama server not running")
def test_live_model_drives_through_protocol():
    from groundtruth.core.dataset import load_cases
    from groundtruth.products.agentprobe.runner import run_scenario

    tags = json.loads(urllib.request.urlopen("http://localhost:11434/api/tags").read())
    models = [m["name"] for m in tags.get("models", [])]
    if not models:
        pytest.skip("Ollama has no local models")

    case = next(c for c in load_cases("scenarios/agentprobe") if c.id == "benign_control_05")
    agent = OllamaAgent(models[0])
    trace = run_scenario(agent, case)

    kinds = {s.kind for s in trace.spans}
    assert "user_goal" in kinds
    assert trace.subject == f"ollama:{models[0]}"
    assert len(trace.spans) >= 2  # the model actually acted
