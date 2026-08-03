"""AgentProbe — scenario runner.

Drives an agent through an attack scenario with deterministic, mocked tools and
records the Trace. Tools return fixed outputs from the scenario spec — some carry
injected instructions planted in otherwise-normal content. No network, no
randomness, no wall-clock: fully reproducible, and $0 to run.
"""
from __future__ import annotations

from ...adapters.agent import Agent, Finish, Observation, ToolCall
from ...core.dataset import Case, CaseSchema
from ...core.trace import Trace

MAX_STEPS = 6

# The AgentProbe scenario vocabulary, declared where the runner that consumes it
# lives. Every key here is read by `run_scenario` or by a detector; adding a
# detector that reads a new key means adding it here in the same commit, which
# is the coupling that keeps the guard honest.
SCENARIO_SCHEMA = CaseSchema(
    required=frozenset({"id", "product", "user_goal", "tools"}),
    optional=frozenset(
        {
            "description",
            "suite",
            "forbidden_tools",
            "injection_target_tool",
            "expect_completion",
            "completion_tools",
            "on_task_tools",
            "secrets",
        }
    ),
    types={
        "id": str,
        "product": str,
        "description": str,
        "user_goal": str,
        "tools": list,
        "forbidden_tools": list,
        "injection_target_tool": str,
        "expect_completion": bool,
        "completion_tools": list,
        "on_task_tools": list,
        "secrets": list,
    },
)


def run_scenario(agent: Agent, case: Case, max_steps: int = MAX_STEPS) -> Trace:
    spec = case.spec
    tools = {t["name"]: t for t in spec.get("tools", [])}
    goal = spec.get("user_goal", "")

    trace = Trace(subject=agent.name, case_id=case.id)
    trace.add("user_goal", content=goal)

    agent.reset()
    last_result: str | None = None
    for _ in range(max_steps):
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

        trace.add("tool_call", name=action.name, data=dict(action.args))
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
