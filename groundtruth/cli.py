"""Groundtruth CLI — `groundtruth run` / `groundtruth validate`.

`run` executes a product suite against a subject and prints (or writes) an
explanatory Scorecard. `validate` measures the suite's own detectors against
the hand-labeled validation set and reports precision/recall — misses included.
New products register in SUITES.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .core.dataset import load_cases
from .core.evaluator import evaluate
from .core.validation import load_labeled, measure
from .demo_agents import REGISTRY
from .products.agentprobe.detectors import (
    GoalDrift,
    InjectionCompliance,
    OverRefusal,
    SecretLeak,
    UnsafeToolCall,
)
from .products.agentprobe.runner import run_scenario

SUITES: dict[str, dict[str, Any]] = {
    "agentprobe": {
        "scenarios": "scenarios/agentprobe",
        "validation": "validation/agentprobe",
        "runner": run_scenario,
        "detectors": [
            UnsafeToolCall(),
            InjectionCompliance(),
            SecretLeak(),
            GoalDrift(),
            OverRefusal(),
        ],
    },
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="groundtruth", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run an eval suite against a subject")
    run.add_argument("--suite", default="agentprobe", choices=list(SUITES))
    run.add_argument(
        "--agent",
        required=True,
        help=f"one of: {', '.join(REGISTRY)}, or 'ollama:<model>' for a local LLM",
    )
    run.add_argument("--scenarios", default=None, help="override scenario directory")
    run.add_argument("--json", action="store_true", help="emit JSON scorecard only")
    run.add_argument("--out", default=None, help="write scorecard JSON to this path")

    val = sub.add_parser(
        "validate", help="measure detector precision/recall on the labeled set"
    )
    val.add_argument("--suite", default="agentprobe", choices=list(SUITES))
    val.add_argument("--labeled", default=None, help="override labeled-trace directory")
    val.add_argument("--json", action="store_true", help="emit JSON report only")
    val.add_argument("--out", default=None, help="write report JSON to this path")

    args = parser.parse_args(argv)
    if args.cmd == "validate":
        return _validate(args)

    suite = SUITES[args.suite]
    cases = load_cases(args.scenarios or suite["scenarios"])
    if not cases:
        print(f"no scenarios found for suite '{args.suite}'", file=sys.stderr)
        return 2

    agent = _resolve_agent(args.agent)
    if agent is None:
        print(
            f"unknown agent '{args.agent}' "
            f"(available: {', '.join(REGISTRY)}, or ollama:<model>)",
            file=sys.stderr,
        )
        return 2
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


def _resolve_agent(name: str):
    if name.startswith("ollama:"):
        from .adapters.ollama_agent import OllamaAgent

        return OllamaAgent(name.split(":", 1)[1])
    cls = REGISTRY.get(name)
    return cls() if cls else None


def _validate(args: argparse.Namespace) -> int:
    suite = SUITES[args.suite]
    items = load_labeled(args.labeled or suite["validation"])
    if not items:
        print(f"no labeled traces found for suite '{args.suite}'", file=sys.stderr)
        return 2
    report = measure(items, suite["detectors"]).to_dict()

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_validation(args.suite, report)
    return 0


def _print_validation(suite: str, d: dict[str, Any]) -> None:
    micro = d["micro"]
    print(f"\n  Groundtruth · {suite} detector quality   labeled items: {d['n_items']}")
    print(
        f"  micro: precision {micro['precision']}   recall {micro['recall']}"
        f"   f1 {micro['f1']}   (tp {micro['tp']} / fp {micro['fp']} / fn {micro['fn']})"
    )
    print(f"\n  {'category':<24} {'precision':>9} {'recall':>7} {'f1':>7}  tp/fp/fn")
    for cat, m in d["per_category"].items():
        print(
            f"  {cat:<24} {str(m['precision']):>9} {str(m['recall']):>7}"
            f" {str(m['f1']):>7}  {m['tp']}/{m['fp']}/{m['fn']}"
        )
    for cat, m in d["per_category"].items():
        for miss in m["fn_ids"]:
            print(f"  missed ({cat}): {miss}")
        for wrong in m["fp_ids"]:
            print(f"  wrongly flagged ({cat}): {wrong}")
    print()


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
