"""Groundtruth CLI — `groundtruth run`.

Runs a product suite against a subject and prints (or writes) an explanatory
Scorecard. v0.1 wires the AgentProbe suite; new products register in SUITES.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .core.dataset import load_cases
from .core.evaluator import evaluate
from .demo_agents import REGISTRY
from .products.agentprobe.detectors import InjectionCompliance, UnsafeToolCall
from .products.agentprobe.runner import run_scenario

SUITES: dict[str, dict[str, Any]] = {
    "agentprobe": {
        "scenarios": "scenarios/agentprobe",
        "runner": run_scenario,
        "detectors": [UnsafeToolCall(), InjectionCompliance()],
    },
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="groundtruth", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run an eval suite against a subject")
    run.add_argument("--suite", default="agentprobe", choices=list(SUITES))
    run.add_argument("--agent", required=True, choices=list(REGISTRY))
    run.add_argument("--scenarios", default=None, help="override scenario directory")
    run.add_argument("--json", action="store_true", help="emit JSON scorecard only")
    run.add_argument("--out", default=None, help="write scorecard JSON to this path")

    args = parser.parse_args(argv)
    if args.cmd != "run":  # argparse enforces this; guard for clarity
        parser.error("unknown command")

    suite = SUITES[args.suite]
    cases = load_cases(args.scenarios or suite["scenarios"])
    if not cases:
        print(f"no scenarios found for suite '{args.suite}'", file=sys.stderr)
        return 2

    agent = REGISTRY[args.agent]()
    traces = {c.id: suite["runner"](agent, c) for c in cases}
    card = evaluate(agent.name, args.suite, cases, traces, suite["detectors"])
    report = card.to_dict()

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_human(report)
    return 0


def _print_human(d: dict[str, Any]) -> None:
    print(f"\n  Groundtruth · {d['suite']}   subject: {d['subject']}")
    print(
        f"  robustness {d['robustness_score']:.2f}"
        f"    cases {d['n_cases']}    failures {d['n_failures']}"
    )
    if d["by_severity"]:
        sev = ", ".join(f"{k}={v}" for k, v in d["by_severity"].items())
        print(f"  severity: {sev}")
    for f in d["failures"]:
        print(f"\n  x [{f['severity']}] {f['case_id']} · {f['category']}  ({f['detector']})")
        print(f"    {f['summary']}")
        for step in f["chain"]:
            print(f"      - {step}")
        print(f"    fix: {f['recommendation']}")
    print()


if __name__ == "__main__":
    sys.exit(main())
