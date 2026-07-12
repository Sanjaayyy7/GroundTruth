"""Groundtruth — Agent adapter.

The single interface every agent-shaped subject implements. AgentProbe subjects
and PlannerBench subjects are agents; JudgeKit's judge model plugs in via a thin
wrapper over the same protocol. An agent observes and emits an Action; the
product runner drives the loop and records the Trace.

Real LLM agents (Ollama / MLX / an OpenAI-compatible API) implement `step` and
plug in here without touching the core. The v0.1 demo subjects are deterministic
and need no model at all.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Union


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class Finish:
    answer: str = ""


Action = Union[ToolCall, Finish]


@dataclass
class Observation:
    user_goal: str
    available_tools: list[str]
    last_tool_result: str | None = None


class Agent(Protocol):
    name: str

    def reset(self) -> None: ...

    def step(self, obs: Observation) -> Action: ...
