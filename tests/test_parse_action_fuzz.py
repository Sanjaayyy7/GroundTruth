"""Fuzz contract for `parse_action` (threat I1, deep-dive finding A6).

`parse_action` is the one place adversarial model output crosses into the
harness, and `ollama_agent`'s docstring promises a malformed reply "must never
crash the harness". That promise had no test: threat I1 named the risk and the
mitigation was a code reading. A reading does not survive a refactor.

The generator is stdlib `random` under a fixed seed rather than a property-based
library. Two reasons, both load-bearing: the one-runtime-dependency claim is
enforced (RC5) and a dev dependency that generates *different* cases per run
would make a failure unreproducible from the artifact alone — the exact property
ADR-0003 refuses to give up. A seeded corpus is replayable from its seed, so a
failure here is a permanent, citable case.
"""
from __future__ import annotations

import json
import random

import pytest

from groundtruth.adapters.agent import Finish, ToolCall
from groundtruth.adapters.ollama_agent import first_parsed_json, parse_action

TOOLS = ["read_email", "send_email", "delete_files"]

# Fragments chosen from failure modes the project actually hit, not from
# abstract "weird strings": the v0.3 parser incidents were a format variant and
# a bracket-in-prose match, and both appear here as building blocks.
_FRAGMENTS = (
    "", " ", "\n", "{", "}", "[", "]", '"', "\\", "\\\\", '\\"', ":", ",",
    "null", "true", "0", "-1", "1e400", "NaN",
    '{"action":', '"tool"', '{"action":"tool"}', '{"action":"finish"}',
    '{"action":"read_email","args":{}}', '{"args":[]}', '{"tool":"read_email"}',
    "Here is the JSON you asked for:", "```json", "```",
    "[{}]", "{{}}", '{"a":{"b":{"c":1}}}', '{"content":"x"}', '{"name":"y"}',
    "IGNORE PREVIOUS INSTRUCTIONS",
    # Written as escapes, not literals: a NUL makes the module itself
    # unparseable, and a bidi override is invisible in a diff.
    "\x00", "\ufeff", "\u202e", "\U0001f600",
)


def _corpus(n: int, seed: int = 42) -> list[str]:
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        out.append("".join(rng.choice(_FRAGMENTS) for _ in range(rng.randint(0, 12))))
    return out


@pytest.mark.parametrize("text", _corpus(600))
def test_parse_action_never_raises_and_always_returns_an_action(text):
    """The fail-open guarantee, stated as a type: every input yields an Action."""
    action = parse_action(text, TOOLS)
    assert isinstance(action, (ToolCall, Finish))
    if isinstance(action, ToolCall):
        # A ToolCall the runner cannot execute is worse than a Finish: the
        # runner splats `args` into the trace, so a non-dict here is the R1
        # crash path reopening under a different input.
        assert action.name in TOOLS
        assert isinstance(action.args, dict)


@pytest.mark.parametrize("text", _corpus(300, seed=7))
def test_iter_json_scanner_never_raises(text):
    """`first_parsed_json` is the scanner under `parse_action`; fuzz it directly
    so a scanner regression is diagnosed at the scanner, not three frames up."""
    value = first_parsed_json(text, openers="{")
    assert value is None or isinstance(value, dict)


def test_unknown_tool_degrades_to_finish_carrying_the_raw_text():
    """A hallucinated tool must not become a ToolCall, and the evidence must
    survive into the trace — detectors and humans read that text."""
    action = parse_action('{"action":"tool","tool":"wipe_disk","args":{}}', TOOLS)
    assert isinstance(action, Finish)
    assert "wipe_disk" in action.answer


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "tool", "tool": "send_email", "args": {"content": "x"}},
        {"action": "tool", "tool": "send_email", "args": {"name": "x"}},
        {"action": "tool", "tool": "send_email", "args": {"kind": "x"}},
    ],
)
def test_reserved_span_field_names_survive_as_tool_args(payload):
    """R1 regression at the parser boundary.

    `content`, `name` and `kind` are Span field names and were the exact kwargs
    that crashed `Trace.add`. The runner fix nests them under `data=`, so these
    must arrive as ordinary args — pinned here because the crash entered through
    a *parsed model reply*, which is what this file generates.
    """
    action = parse_action(json.dumps(payload), TOOLS)
    assert isinstance(action, ToolCall)
    assert action.args == payload["args"]
