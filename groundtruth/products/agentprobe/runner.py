"""AgentProbe — scenario runner.

Drives an agent through an attack scenario with deterministic, mocked tools and
records the Trace. Tools return fixed outputs from the scenario spec — some carry
injected instructions planted in otherwise-normal content. No network, no
randomness, no wall-clock: fully reproducible, and $0 to run.
"""
from __future__ import annotations

from ...adapters.agent import Agent, Finish, Observation, ToolCall
from ...core.dataset import Case
from ...core.trace import Trace

MAX_STEPS = 6


def run_scenario(agent: Agent, case: Case) -> Trace:
    spec = case.spec
    tools = {t["name"]: t for t in spec.get("tools", [])}
    goal = spec.get("user_goal", "")

    trace = Trace(subject=agent.name, case_id=case.id)
    trace.add("user_goal", content=goal)

    agent.reset()
    last_result: str | None = None
    for _ in range(MAX_STEPS):
        obs = Observation(
            user_goal=goal,
            available_tools=list(tools),
            last_tool_result=last_result,
        )
        action = agent.step(obs)

        if isinstance(action, Finish):
            trace.add("final", content=action.answer)
            break

        if not isinstance(action, ToolCall):  # defensive: unknown action type
            trace.add("final", content="<invalid action>")
            break

        trace.add("tool_call", name=action.name, **dict(action.args))
        tool = tools.get(action.name)
        if tool is None:
            last_result = f"error: unknown tool '{action.name}'"
            trace.add("tool_result", name=action.name, content=last_result, restricted=False)
            continue
        last_result = tool.get("returns", "")
        trace.add(
            "tool_result",
            name=action.name,
            content=last_result,
            restricted=bool(tool.get("restricted", False)),
        )
    return trace
