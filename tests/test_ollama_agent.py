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


class _RecordingChat:
    """Fake chat_fn (judge-style injection): records every message list it
    receives and plays back scripted replies. Zero network."""

    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.calls: list[list[dict[str, str]]] = []

    def __call__(self, messages: list[dict[str, str]]) -> str:
        self.calls.append([dict(m) for m in messages])
        return self.replies.pop(0)


def _obs(last_result: str | None = None):
    from groundtruth.adapters.agent import Observation

    return Observation(
        user_goal="Read my latest email and summarize it.",
        available_tools=TOOLS,
        last_tool_result=last_result,
    )


def test_stateless_default_never_accumulates_history():
    """Pins the published v0.3 behavior: every step is built from the
    Observation alone — system + one user message, regardless of step count."""
    fake = _RecordingChat(
        ['{"action": "tool", "tool": "read_email"}'] * 2
    )
    agent = OllamaAgent("m", chat_fn=fake)
    agent.reset()

    agent.step(_obs())
    agent.step(_obs(last_result="From: teammate@company.com ..."))

    assert [len(c) for c in fake.calls] == [2, 2]
    assert all(c[0]["role"] == "system" for c in fake.calls)


def test_stateful_variant_carries_full_history():
    """The stall-confound instrument: the model must see its own prior
    actions. Step 2's prompt contains the step-1 assistant reply and the
    tool result — the prompt is no longer a fixed point."""
    first_reply = '{"action": "tool", "tool": "read_email"}'
    fake = _RecordingChat([first_reply, '{"action": "finish", "answer": "done"}'])
    agent = OllamaAgent("m", stateful=True, chat_fn=fake)
    agent.reset()

    agent.step(_obs())
    agent.step(_obs(last_result="From: teammate@company.com ..."))

    second = fake.calls[1]
    assert len(second) == 4  # system, task, assistant reply, tool result
    assert second[2] == {"role": "assistant", "content": first_reply}
    assert second[3]["role"] == "user"
    assert "From: teammate@company.com" in second[3]["content"]


def test_stateful_reset_clears_history_between_episodes():
    fake = _RecordingChat(
        ['{"action": "tool", "tool": "read_email"}'] * 2
    )
    agent = OllamaAgent("m", stateful=True, chat_fn=fake)

    agent.reset()
    agent.step(_obs())
    agent.reset()
    agent.step(_obs())

    assert [len(c) for c in fake.calls] == [2, 2]  # no leak across episodes


def test_stateful_subject_name_is_distinguishable():
    """Traces are evidence artifacts; a stateful run must never be mistaken
    for a published stateless run of the same model."""
    assert OllamaAgent("m", stateful=True, chat_fn=lambda m: "").name == "ollama:m+stateful"
    assert OllamaAgent("m", chat_fn=lambda m: "").name == "ollama:m"


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
