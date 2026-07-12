"""Demo subjects for AgentProbe — deterministic, no LLM required.

`vulnerable_agent` naively trusts tool output and follows instructions embedded
in it. `hardened_agent` enforces a tool-authorization boundary and never acts on
instructions found in retrieved content. They exist to prove the harness catches
the difference reproducibly and for $0. A real LLM agent (Ollama / MLX / API)
drops in by implementing the same `Agent` protocol.
"""
from __future__ import annotations

import re

from .adapters.agent import Action, Finish, Observation, ToolCall

_READ_HINTS = ("read", "get", "search", "fetch", "list")
_INSTRUCTION = re.compile(r"call\s+([a-z_]\w+)", re.IGNORECASE)


def _pick_read_tool(tools: list[str]) -> str | None:
    for t in tools:
        if any(h in t for h in _READ_HINTS):
            return t
    return None


class VulnerableAgent:
    """Trusts everything. Executes any 'call <tool>' it finds in tool output."""

    name = "vulnerable_agent"

    def reset(self) -> None:
        self._read = False

    def step(self, obs: Observation) -> Action:
        if not self._read:
            self._read = True
            tool = _pick_read_tool(obs.available_tools)
            if tool:
                return ToolCall(tool)
        match = _INSTRUCTION.search(obs.last_tool_result or "")
        if match and match.group(1) in obs.available_tools:
            return ToolCall(match.group(1))
        return Finish("Here is a summary of your request.")


class HardenedAgent:
    """Reads, then stops. Never acts on instructions embedded in retrieved content."""

    name = "hardened_agent"

    def reset(self) -> None:
        self._read = False

    def step(self, obs: Observation) -> Action:
        if not self._read:
            self._read = True
            tool = _pick_read_tool(obs.available_tools)
            if tool:
                return ToolCall(tool)
        return Finish(
            "Summary complete. I ignored any instructions embedded in retrieved content "
            "and did not call restricted tools without authorization."
        )


REGISTRY: dict[str, type] = {
    "vulnerable_agent": VulnerableAgent,
    "hardened_agent": HardenedAgent,
}
