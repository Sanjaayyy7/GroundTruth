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
from .products.agentprobe.demo_agents import REGISTRY
from .products.agentprobe.detectors import (
    GoalDrift,
    InjectionCompliance,
    NonCompletion,
    OverRefusal,
    SecretLeak,
    UnsafeToolCall,
)
from .products.agentprobe.judge import LLMJudge
from .products.agentprobe.runner import run_scenario

# Data directories resolve against the repo root, not the caller's cwd, so the
# CLI works from anywhere (and inside CI checkouts).
_REPO_ROOT = Path(__file__).resolve().parents[1]

SUITES: dict[str, dict[str, Any]] = {
    "agentprobe": {
        "scenarios": _REPO_ROOT / "scenarios/agentprobe",
        "validation": _REPO_ROOT / "validation/agentprobe",
        "runner": run_scenario,
        "detectors": [
            UnsafeToolCall(),
            InjectionCompliance(),
            SecretLeak(),
            GoalDrift(),
            OverRefusal(),
            NonCompletion(),
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
    run.add_argument(
        "--traces-out",
        default=None,
        help="also write each raw trace as trace-<case_id>.json into this directory",
    )
    run.add_argument(
        "--stateful",
        action="store_true",
        help="give an ollama:<model> subject its own message history within each "
        "episode (second measurement condition; subject is named <model>+stateful)",
    )

    val = sub.add_parser(
        "validate", help="measure detector precision/recall on the labeled set"
    )
    val.add_argument("--suite", default="agentprobe", choices=list(SUITES))
    val.add_argument("--labeled", default=None, help="override labeled-trace directory")
    val.add_argument(
        "--judge",
        default=None,
        help="measure an LLM judge (e.g. 'ollama:llama3.1:8b') instead of the rules",
    )
    val.add_argument("--json", action="store_true", help="emit JSON report only")
    val.add_argument("--out", default=None, help="write report JSON to this path")

    rep = sub.add_parser(
        "report", help="render runs/ artifacts into one self-contained HTML report"
    )
    rep.add_argument("--runs", default=None, help="directory holding scorecard-*.json")
    rep.add_argument("--out", default=None, help="output HTML path (default <runs>/report.html)")

    ci = sub.add_parser(
        "ci", help="fail (exit 1) when the subject regresses vs a stored baseline"
    )
    ci.add_argument("--suite", default="agentprobe", choices=list(SUITES))
    ci.add_argument("--agent", required=True)
    ci.add_argument("--baseline", default=None, help="baseline scorecard JSON path")
    ci.add_argument(
        "--update", action="store_true", help="write the current scorecard as the baseline"
    )

    aud = sub.add_parser(
        "audit",
        help="audit evaluation evidence: contracts, quality manifest, assurance report",
    )
    aud.add_argument("--root", default=None, help="evaluation root (default: this repo)")
    aud.add_argument("--claims", default=None, help="claims register path")
    aud.add_argument("--threats", default=None, help="threats register path")
    aud.add_argument(
        "--out", default=None, help="manifest path (default <root>/runs/quality-manifest.json)"
    )
    aud.add_argument(
        "--report",
        default=None,
        help="assurance report path (default <root>/runs/assurance-report.md)",
    )
    aud.add_argument("--json", action="store_true", help="print the manifest JSON to stdout")

    args = parser.parse_args(argv)
    if args.cmd == "validate":
        return _validate(args)
    if args.cmd == "ci":
        return _ci(args)
    if args.cmd == "report":
        return _report(args)
    if args.cmd == "audit":
        return _audit(args)

    suite = SUITES[args.suite]
    cases = load_cases(args.scenarios or suite["scenarios"])
    if not cases:
        print(f"no scenarios found for suite '{args.suite}'", file=sys.stderr)
        return 2

    if args.stateful and not args.agent.startswith("ollama:"):
        print(
            f"--stateful requires an ollama:<model> subject; '{args.agent}' is a "
            "scripted agent with no context window",
            file=sys.stderr,
        )
        return 2
    agent = _resolve_agent(args.agent, stateful=args.stateful)
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

    if args.traces_out:
        traces_dir = Path(args.traces_out)
        traces_dir.mkdir(parents=True, exist_ok=True)
        for case_id, trace in traces.items():
            (traces_dir / f"trace-{case_id}.json").write_text(
                json.dumps(trace.to_dict(), indent=2)
            )
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_human(report)
    return 0


def _resolve_agent(name: str, stateful: bool = False):
    if name.startswith("ollama:"):
        from .adapters.ollama_agent import OllamaAgent

        return OllamaAgent(name.split(":", 1)[1], stateful=stateful)
    cls = REGISTRY.get(name)
    return cls() if cls else None


def _ci(args: argparse.Namespace) -> int:
    suite = SUITES[args.suite]
    agent = _resolve_agent(args.agent)
    if agent is None:
        print(f"unknown agent '{args.agent}'", file=sys.stderr)
        return 2
    cases = load_cases(suite["scenarios"])
    traces = {c.id: suite["runner"](agent, c) for c in cases}
    current = evaluate(agent.name, args.suite, cases, traces, suite["detectors"]).to_dict()

    default_name = f"baseline-{args.agent.replace(':', '-')}.json"
    baseline_path = Path(args.baseline) if args.baseline else _REPO_ROOT / "runs" / default_name

    if args.update:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(current, indent=2))
        print(f"baseline written: {baseline_path} (robustness {current['robustness_score']})")
        return 0

    if not baseline_path.exists():
        print(
            f"no baseline at {baseline_path} — create one with --update", file=sys.stderr
        )
        return 2

    baseline = json.loads(baseline_path.read_text())
    base_failed = {f["case_id"] for f in baseline["failures"]}
    cur_failed = {f["case_id"] for f in current["failures"]}
    newly_failing = sorted(cur_failed - base_failed)
    score_drop = current["robustness_score"] < baseline["robustness_score"]

    print(
        f"  Groundtruth CI · {args.suite}   subject: {current['subject']}\n"
        f"  baseline robustness {baseline['robustness_score']}  ->  current {current['robustness_score']}"
    )
    if newly_failing or score_drop:
        print("  SAFETY REGRESSION")
        for case_id in newly_failing:
            categories = sorted(
                {f["category"] for f in current["failures"] if f["case_id"] == case_id}
            )
            print(f"    newly failing: {case_id}  ({', '.join(categories)})")
        return 1
    if cur_failed != base_failed or current["robustness_score"] > baseline["robustness_score"]:
        print("  improvement vs baseline — consider refreshing it with --update")
    else:
        print("  no regression")
    return 0


def _report(args: argparse.Namespace) -> int:
    from .core.report import render_html

    runs_dir = Path(args.runs) if args.runs else _REPO_ROOT / "runs"
    cards = [json.loads(p.read_text()) for p in sorted(runs_dir.glob("scorecard-*.json"))]
    if not cards:
        print(f"no scorecard-*.json artifacts in {runs_dir}", file=sys.stderr)
        return 2
    quality_path = runs_dir / "detector-quality.json"
    quality = json.loads(quality_path.read_text()) if quality_path.exists() else None

    out = Path(args.out) if args.out else runs_dir / "report.html"
    out.write_text(render_html(cards, quality=quality))
    print(f"report written: {out} ({len(cards)} subjects)")
    return 0


def _audit(args: argparse.Namespace) -> int:
    from .meta.assurance import render_assurance
    from .meta.contracts import run_contracts
    from .meta.graph import build_graph
    from .meta.loader import RegisterError, load_evidence
    from .meta.manifest import build_manifest, render_manifest

    root = Path(args.root) if args.root else _REPO_ROOT
    try:
        nodes = load_evidence(
            root,
            claims_path=Path(args.claims) if args.claims else None,
            threats_path=Path(args.threats) if args.threats else None,
        )
    except RegisterError as exc:
        print(f"[audit] {exc}", file=sys.stderr)
        return 2

    graph = build_graph(nodes)
    findings = run_contracts(graph)
    manifest = build_manifest(graph, findings)

    out = Path(args.out) if args.out else root / "runs/quality-manifest.json"
    report = Path(args.report) if args.report else root / "runs/assurance-report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_manifest(manifest))
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_assurance(graph, findings))

    if args.json:
        print(render_manifest(manifest), end="")
    else:
        n = manifest["graph"]
        print(
            f"\n  Groundtruth audit · {manifest['evaluation']['name']}"
            f" @ {manifest['evaluation']['harness_commit']}"
        )
        print(f"  evidence graph: {n['nodes']} nodes / {n['edges']} edges")
        if findings:
            print(f"  CONTRACT FINDINGS ({len(findings)}):")
            for f in findings:
                print(f"    x [{f.contract_id}] {f.node_id}: {f.summary}")
        else:
            print("  all contracts hold")
        print(f"  manifest: {out}\n  assurance: {report}\n")
    return 1 if findings else 0


def _validate(args: argparse.Namespace) -> int:
    suite = SUITES[args.suite]
    items = load_labeled(args.labeled or suite["validation"])
    if not items:
        print(f"no labeled traces found for suite '{args.suite}'", file=sys.stderr)
        return 2
    detectors = suite["detectors"]
    if args.judge:
        model = args.judge.removeprefix("ollama:")
        detectors = [LLMJudge(model)]
    report = measure(items, detectors).to_dict()

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
