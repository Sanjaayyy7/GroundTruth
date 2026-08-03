"""Configuration contract (Config 5/10 finding).

The defect was never "these are constants" — it was that `max_steps` existed
in the runner and in an experiment script but not on the CLI, so the README's
step-budget claim was not reproducible with the published binary. Host and
timeout follow the GROUNDTRUTH_ROOT precedent: environment override, no flag,
because they describe the machine rather than the measurement.

Seed and temperature stay constants on purpose. ADR-0003 makes determinism a
property of the published evidence, and a configurable seed turns every
scorecard into "0.375 at some seed" — a number that cannot be compared across
versions. There is no test asserting they are absent; there is this note, and
the absence of a flag.
"""
from __future__ import annotations

import json

import pytest

from groundtruth.adapters.ollama_agent import _DEFAULT_HOST, _DEFAULT_TIMEOUT, OllamaAgent
from groundtruth.cli import main
from groundtruth.products.agentprobe.runner import MAX_STEPS


def test_run_accepts_max_steps(capsys):
    rc = main(["run", "--agent", "hardened_agent", "--max-steps", "24", "--json"])

    assert rc == 0
    assert json.loads(capsys.readouterr().out)["n_cases"] > 0


def test_max_steps_default_is_the_published_budget(capsys):
    """Every published number was measured at 6. The flag must not move it."""
    rc = main(["run", "--agent", "hardened_agent", "--json"])
    default = capsys.readouterr().out

    assert rc == 0
    rc = main(["run", "--agent", "hardened_agent", "--max-steps", str(MAX_STEPS), "--json"])

    assert rc == 0
    assert capsys.readouterr().out == default


def test_max_steps_below_one_is_rejected_not_silently_clamped(capsys):
    rc = main(["run", "--agent", "hardened_agent", "--max-steps", "0"])

    assert rc == 2
    assert "--max-steps" in capsys.readouterr().err


def test_max_steps_changes_the_budget_the_runner_receives(monkeypatch, capsys):
    seen: list[int] = []
    import groundtruth.cli as cli

    real = cli.SUITES["agentprobe"]["runner"]

    def spy(agent, case, max_steps=6):
        seen.append(max_steps)
        return real(agent, case, max_steps=max_steps)

    monkeypatch.setitem(cli.SUITES["agentprobe"], "runner", spy)
    main(["run", "--agent", "hardened_agent", "--max-steps", "12", "--json"])

    assert set(seen) == {12}


def test_host_and_timeout_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("GROUNDTRUTH_OLLAMA_HOST", "http://elsewhere:1234/")
    monkeypatch.setenv("GROUNDTRUTH_OLLAMA_TIMEOUT", "7")

    agent = OllamaAgent("llama3.1:8b")

    assert agent.host == "http://elsewhere:1234"
    assert agent.timeout == 7


def test_environment_defaults_match_the_published_constants(monkeypatch):
    monkeypatch.delenv("GROUNDTRUTH_OLLAMA_HOST", raising=False)
    monkeypatch.delenv("GROUNDTRUTH_OLLAMA_TIMEOUT", raising=False)

    agent = OllamaAgent("llama3.1:8b")

    assert (agent.host, agent.timeout) == (_DEFAULT_HOST, _DEFAULT_TIMEOUT)


def test_a_malformed_timeout_is_a_loud_error_not_a_silent_default(monkeypatch):
    monkeypatch.setenv("GROUNDTRUTH_OLLAMA_TIMEOUT", "soon")

    with pytest.raises(ValueError, match="GROUNDTRUTH_OLLAMA_TIMEOUT"):
        OllamaAgent("llama3.1:8b")
