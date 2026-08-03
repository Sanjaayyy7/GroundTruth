"""Groundtruth CLI — `groundtruth run` / `groundtruth validate`.

`run` executes a product suite against a subject and prints (or writes) an
explanatory Scorecard. `validate` measures the suite's own detectors against
the hand-labeled validation set and reports precision/recall — misses included.
New products register in SUITES.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .adapters.agent import Agent
from .core.dataset import Case, load_cases
from .core.evaluator import TraceNotFound, evaluate
from .core.trace import Trace
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
from .products.agentprobe.runner import MAX_STEPS, run_scenario

# Data directories resolve against the repo root, not the caller's cwd, so the
# CLI works from anywhere (and inside CI checkouts).
_DEFAULT_ROOT = Path(__file__).resolve().parents[1]

_LOG = logging.getLogger(__name__)
_LEVELS = (logging.WARNING, logging.INFO, logging.DEBUG)


def _configure_logging(verbosity: int) -> None:
    """Diagnostics on stderr, never stdout, and never with a timestamp.

    stdout is an interface here — human scorecards a README quotes, JSON a
    consumer parses — and every artifact under runs/ is byte-diffed in CI, so a
    single wall-clock string reaching a stream that gets captured would churn a
    committed diff forever. The handler is attached to the `groundtruth` logger
    rather than the root logger so importing this package as a library does not
    silently reconfigure the host application's logging."""
    log = logging.getLogger("groundtruth")
    log.handlers.clear()
    log.setLevel(_LEVELS[min(verbosity, len(_LEVELS) - 1)])
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
    log.addHandler(handler)
    log.propagate = False


@contextlib.contextmanager
def _timed(what: str) -> Iterator[None]:
    """Duration of one phase, at INFO. Timings are diagnostics, not evidence:
    they never enter a scorecard, a manifest or any other artifact."""
    start = time.perf_counter()
    yield
    _LOG.info("%s took %.2fs", what, time.perf_counter() - start)


class SourceInstallRequired(RuntimeError):
    """The corpus is not reachable from the resolved root. CLI exit code 2."""


class RescoreError(RuntimeError):
    """A rescore cannot proceed from the committed traces. CLI exit code 2."""


def _package_version() -> str:
    """Declared package version. Imported lazily so the steward's manifest can
    name the milestone it describes without cli importing the package eagerly."""
    from . import __version__

    return __version__


def _repo_root() -> Path:
    """Root that the corpus and default artifact paths resolve against.

    GROUNDTRUTH_ROOT overrides it. A non-editable `pip install .` puts this
    module under site-packages, where the corpus is absent: scenarios and
    labeled traces are evaluation data, not package code, and are deliberately
    not shipped inside the wheel."""
    env = os.environ.get("GROUNDTRUTH_ROOT")
    return Path(env).expanduser().resolve() if env else _DEFAULT_ROOT


def _corpus_root() -> Path:
    root = _repo_root()
    _LOG.info("corpus root: %s", root)
    missing = [d for d in ("scenarios", "validation") if not (root / d).is_dir()]
    if missing:
        raise SourceInstallRequired(
            f"no {' or '.join(missing)} directory under {root} — Groundtruth resolves "
            f"its scenario and validation corpus relative to a source checkout, and "
            f"that corpus is not shipped inside the installed package. Either install "
            f"from a clone in place (`pip install -e .`), or point GROUNDTRUTH_ROOT at "
            f"the checkout (`GROUNDTRUTH_ROOT=/path/to/groundtruth groundtruth ...`)"
        )
    return root


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
            NonCompletion(),
        ],
    },
}


def main(argv: list[str] | None = None) -> int:
    # `-v` is global: declared once and attached to the root parser and to every
    # verb, so both `groundtruth -v run` and `groundtruth run -v` work. The
    # SUPPRESS default is load-bearing — without it the verb's parser would
    # overwrite a value the root parser already collected.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=argparse.SUPPRESS,
        help="diagnostics on stderr (-v phases and subjects, -vv git and cases)",
    )

    parser = argparse.ArgumentParser(
        prog="groundtruth", description=__doc__, parents=[common]
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser(
        "run", help="run an eval suite against a subject", parents=[common]
    )
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
        "--max-steps",
        type=int,
        default=MAX_STEPS,
        help=f"tool-call budget per episode (default {MAX_STEPS}; every published "
        f"number was measured at the default — changing it makes a new measurement, "
        f"not a comparable one)",
    )
    run.add_argument(
        "--stateful",
        action="store_true",
        help="give an ollama:<model> subject its own message history within each "
        "episode (second measurement condition; subject is named <model>+stateful)",
    )

    res = sub.add_parser(
        "rescore",
        help="re-score committed traces with the current detectors (no model required)",
        parents=[common],
    )
    res.add_argument("--suite", default="agentprobe", choices=list(SUITES))
    res.add_argument(
        "--subject",
        default=None,
        help="trace-directory slug under --traces (default: every slug present)",
    )
    res.add_argument("--traces", default=None, help="trace root (default <root>/runs/traces)")
    res.add_argument(
        "--runs", default=None, help="scorecard directory (default <root>/runs)"
    )
    res.add_argument(
        "--check",
        action="store_true",
        help="regenerate in memory and diff against the committed scorecards; "
        "exit 1 on any difference and write nothing (this is what CI calls)",
    )

    val = sub.add_parser(
        "validate",
        help="measure detector precision/recall on the labeled set",
        parents=[common],
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
        "report",
        help="render runs/ artifacts into one self-contained HTML report",
        parents=[common],
    )
    rep.add_argument("--runs", default=None, help="directory holding scorecard-*.json")
    rep.add_argument("--out", default=None, help="output HTML path (default <runs>/report.html)")

    ci = sub.add_parser(
        "ci",
        help="fail (exit 1) when the subject regresses vs a stored baseline",
        parents=[common],
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
        parents=[common],
    )
    aud.add_argument("--root", default=None, help="evaluation root (default: this repo)")
    aud.add_argument(
        "--name",
        default="groundtruth",
        help="evaluation name recorded in the manifest (set this when "
        "auditing another evaluation's registers via --root)",
    )
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

    ste = sub.add_parser(
        "steward",
        help="audit the repository against the Constitution (RC1-RC8, advisory)",
        parents=[common],
    )
    ste.add_argument("--root", default=None, help="repository root (default: this repo)")
    ste.add_argument(
        "--out", default=None, help="artifact directory (default <root>/runs/steward)"
    )
    ste.add_argument("--json", action="store_true", help="print the manifest JSON to stdout")

    args = parser.parse_args(argv)
    _configure_logging(getattr(args, "verbose", 0) or 0)
    _LOG.info("verb: %s", args.cmd)
    if args.cmd == "steward":
        return _steward(args)
    if args.cmd == "rescore":
        return _rescore(args)
    if args.cmd == "validate":
        return _validate(args)
    if args.cmd == "ci":
        return _ci(args)
    if args.cmd == "report":
        return _report(args)
    if args.cmd == "audit":
        return _audit(args)

    suite = SUITES[args.suite]
    try:
        scenarios = Path(args.scenarios) if args.scenarios else _corpus_root() / suite["scenarios"]
    except SourceInstallRequired as exc:
        print(f"[run] {exc}", file=sys.stderr)
        return 2
    cases = load_cases(scenarios)
    if not cases:
        print(f"no scenarios found for suite '{args.suite}'", file=sys.stderr)
        return 2
    if args.max_steps < 1:
        print(
            f"--max-steps must be at least 1, got {args.max_steps}", file=sys.stderr
        )
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
    from .adapters.ollama_agent import OllamaUnavailable

    _LOG.info(
        "subject %s over %d case(s), max_steps=%d", agent.name, len(cases), args.max_steps
    )
    try:
        traces = {}
        for case in cases:
            # Case ids only. A trace body is adversarial by construction and a
            # log is not a quarantine, so nothing from inside it is logged.
            _LOG.debug("case %s -> %s", case.id, agent.name)
            with _timed(f"case {case.id}"):
                traces[case.id] = suite["runner"](agent, case, max_steps=args.max_steps)
        with _timed("scoring"):
            card = evaluate(agent.name, args.suite, cases, traces, suite["detectors"])
    except (OllamaUnavailable, TraceNotFound) as exc:
        print(f"[run] {exc}", file=sys.stderr)
        return 2
    report = card.to_dict()

    if args.traces_out:
        traces_dir = Path(args.traces_out)
        traces_dir.mkdir(parents=True, exist_ok=True)
        for case_id, trace in traces.items():
            (traces_dir / f"trace-{case_id}.json").write_text(
                json.dumps(trace.to_dict(), indent=2)
            )
    if args.out:
        _write_json(Path(args.out), report)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_human(report)
    return 0


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """The single serialization for every JSON artifact this CLI emits, so that
    `run`, `ci` and `rescore` produce byte-identical files for identical content
    — rescoring an unchanged detector set must not churn the diff."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def _resolve_agent(name: str, stateful: bool = False) -> Agent | None:
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
    try:
        cases = load_cases(_corpus_root() / suite["scenarios"])
    except SourceInstallRequired as exc:
        print(f"[ci] {exc}", file=sys.stderr)
        return 2
    traces = {c.id: suite["runner"](agent, c) for c in cases}
    try:
        current = evaluate(agent.name, args.suite, cases, traces, suite["detectors"]).to_dict()
    except TraceNotFound as exc:
        print(f"[ci] {exc}", file=sys.stderr)
        return 2

    default_name = f"baseline-{args.agent.replace(':', '-')}.json"
    baseline_path = Path(args.baseline) if args.baseline else _repo_root() / "runs" / default_name

    if args.update:
        _write_json(baseline_path, current)
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
        # Finding D4. This branch used to print advice and return 0, which made
        # the gate blind in the one direction it cannot afford to be: a detector
        # that regresses and stops firing raises robustness and PASSES. It also
        # left the baseline stale, and a stale baseline under-constrains the
        # next comparison — a later slide back part-way then reads as "no
        # regression". So an improvement is a finding. The two legal exits are
        # the Constitution's own (Law 10): fix the repository, or amend the
        # declared baseline with justification. Never "carry on".
        print("  UNEXPLAINED IMPROVEMENT — the baseline no longer describes this subject")
        for case_id in sorted(base_failed - cur_failed):
            print(f"    stopped failing: {case_id}")
        print(
            "    either refresh the baseline with --update, in the commit that\n"
            "    earned the improvement, or find the detector that stopped firing"
        )
        return 1
    print("  no regression")
    return 0


def _rescore(args: argparse.Namespace) -> int:
    """Re-derive scorecards from committed traces. A trace is the durable record
    of a run; without this path a detector change cannot reach the published
    artifacts and CI cannot tell whether they have gone stale (finding R4)."""
    suite = SUITES[args.suite]
    try:
        cases = load_cases(_corpus_root() / suite["scenarios"])
    except SourceInstallRequired as exc:
        print(f"[rescore] {exc}", file=sys.stderr)
        return 2
    traces_root = Path(args.traces) if args.traces else _repo_root() / "runs" / "traces"
    runs_dir = Path(args.runs) if args.runs else _repo_root() / "runs"

    try:
        slugs = _rescore_slugs(traces_root, args.subject)
        cards = {s: _rescore_one(traces_root / s, args.suite, cases, suite) for s in slugs}
    except (RescoreError, TraceNotFound) as exc:
        print(f"[rescore] {exc}", file=sys.stderr)
        return 2

    if not args.check:
        for slug, card in cards.items():
            _write_json(runs_dir / f"scorecard-{slug}.json", card)
        print(f"\n  rescore · wrote {len(cards)} scorecard(s) to {runs_dir}\n")
        return 0

    drifted: dict[str, list[str]] = {}
    for slug, card in cards.items():
        path = runs_dir / f"scorecard-{slug}.json"
        committed = json.loads(path.read_text()) if path.exists() else None
        if committed is None:
            drifted[slug] = ["<no committed scorecard>"]
        elif committed != card:
            drifted[slug] = sorted(
                k for k in set(committed) | set(card) if committed.get(k) != card.get(k)
            )
    print(f"\n  rescore --check · {len(cards)} scorecard(s) vs {runs_dir}")
    if not drifted:
        print("  all identical to the committed artifacts\n")
        return 0
    print(f"  STALE ARTIFACTS ({len(drifted)}):")
    for slug, keys in drifted.items():
        print(f"    x scorecard-{slug}.json differs in: {', '.join(keys)}")
    print("  regenerate with: groundtruth rescore\n")
    return 1


def _rescore_slugs(traces_root: Path, subject: str | None) -> list[str]:
    available = sorted(p.name for p in traces_root.iterdir() if p.is_dir()) \
        if traces_root.is_dir() else []
    if not available:
        raise RescoreError(
            f"no trace directories under {traces_root} — rescore reads the traces a "
            f"previous `run --traces-out` committed; point --traces at that directory"
        )
    if subject is None:
        return available
    if subject not in available:
        raise RescoreError(
            f"no traces for subject '{subject}' under {traces_root} — the subject is the "
            f"trace directory slug, not the model name. Available: {', '.join(available)}"
        )
    return [subject]


def _rescore_one(
    directory: Path, suite_name: str, cases: list[Case], suite: dict[str, Any]
) -> dict[str, Any]:
    """The trace files carry their own `subject`, so the slug <-> subject mapping
    is read from the data rather than reconstructed from the directory name."""
    traces: dict[str, Trace] = {}
    subjects: set[str] = set()
    for path in sorted(directory.glob("trace-*.json")):
        trace = Trace.from_dict(json.loads(path.read_text()))
        traces[trace.case_id] = trace
        subjects.add(trace.subject)
    if len(subjects) > 1:
        raise RescoreError(
            f"{directory} mixes {len(subjects)} subjects ({', '.join(sorted(subjects))}) — "
            f"one trace directory records exactly one subject-condition; split them"
        )
    subject = subjects.pop() if subjects else directory.name
    return evaluate(subject, suite_name, cases, traces, suite["detectors"]).to_dict()


def _report(args: argparse.Namespace) -> int:
    from .core.report import render_html

    runs_dir = Path(args.runs) if args.runs else _repo_root() / "runs"
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

    root = Path(args.root) if args.root else _repo_root()
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
    manifest = build_manifest(graph, findings, evaluation_name=args.name)

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


def _steward(args: argparse.Namespace) -> int:
    from .steward.checks import run_checks
    from .steward.inventory import build_inventory
    from .steward.loader import (
        git_blob_sizes,
        git_index,
        load_constitution,
        load_debt,
    )
    from .steward.model import DeclarationError
    from .steward.report import render_manifest, render_report, trigger_ledger

    root = Path(args.root) if args.root else _repo_root()
    try:
        decls = load_constitution(root / "docs/CONSTITUTION.md")
        debt = load_debt(root / "docs/debt.yaml")
        index = git_index(root)
        sizes = git_blob_sizes(root)
    except DeclarationError as exc:
        print(f"[steward] {exc}", file=sys.stderr)
        return 2

    inventory = build_inventory(index, decls.roles, sizes)
    active, exempted = run_checks(root, decls, debt, index)

    # The ledger travels in the manifest so the firing record is byte-checked
    # like every other piece of committed evidence; a trigger nobody can audit
    # is the prose promise this replaces.
    inventory["trigger_ledger"] = trigger_ledger(active, exempted, _package_version())

    out_dir = Path(args.out) if args.out else root / "runs/steward"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "repo-manifest.json").write_text(render_manifest(inventory))
    (out_dir / "steward-report.md").write_text(
        render_report(active, exempted, decls, inventory)
    )

    if args.json:
        print(render_manifest(inventory), end="")
    else:
        total = inventory["total"]
        print(f"\n  Groundtruth steward · {total['files']} tracked files")
        if active:
            print(f"  REPOSITORY FINDINGS ({len(active)}):")
            for f in active:
                loc = f"{f.path}:{f.line}" if f.line else f.path
                print(f"    x [{f.check_id}] {loc}: {f.summary}")
        else:
            print("  all repository contracts hold")
        if decls.exemptions:
            print(f"  active exemptions: {len(decls.exemptions)} ({len(exempted)} findings exempted)")
        print(f"  manifest: {out_dir / 'repo-manifest.json'}")
        print(f"  report: {out_dir / 'steward-report.md'}\n")
    return 1 if active else 0


def _validate(args: argparse.Namespace) -> int:
    suite = SUITES[args.suite]
    try:
        labeled = Path(args.labeled) if args.labeled else _corpus_root() / suite["validation"]
    except SourceInstallRequired as exc:
        print(f"[validate] {exc}", file=sys.stderr)
        return 2
    items = load_labeled(labeled)
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
    macro = d["macro"]
    print(
        f"  micro: precision {micro['precision']}   recall {micro['recall']}"
        f"   f1 {micro['f1']}   (tp {micro['tp']} / fp {micro['fp']} / fn {micro['fn']})"
    )
    print(
        f"  macro: precision {macro['precision']}   recall {macro['recall']}"
        f"   f1 {macro['f1']}   (unweighted over {macro['n_categories']} categories)"
    )
    print(f"\n  {'category':<24} {'precision':>9} {'recall':>7} {'f1':>7}  tp/fp/fn")
    for cat, m in d["per_category"].items():
        print(
            f"  {cat:<24} {m['precision']!s:>9} {m['recall']!s:>7}"
            f" {m['f1']!s:>7}  {m['tp']}/{m['fp']}/{m['fn']}"
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
