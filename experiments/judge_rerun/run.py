"""Judge-rerun experiment runner — two confounds, four arms, two subjects.

The protocol was committed BEFORE this script ever ran: see
`docs/specs/2026-08-02-judge-rerun-preregistration.md` (commit `3d00783`) for
the question, the arms, the five predictions, and the stop rule. This file
executes that protocol and nothing else.

Every arm measures the same 68 labeled traces through the same Validation
Engine the rule detectors go through, at temperature 0 and seed 42, so the
only thing that varies between arms is the variable the arm names.

Arm A0 is a gate, not a result. It restores the pre-`2263f9c` parser to
reproduce the published precision; if it does not reproduce within the
pre-registered +/-0.03, every later arm is uninterpretable and the experiment
stops (protocol, "Design").

Run from the repo root:
    ./.venv/bin/python experiments/judge_rerun/run.py
Resumable: a cell whose metric artifact already exists is skipped unless
--force is passed, because 8 x 68 sequential local model calls is a long
enough run that losing completed work to a crash is a real cost.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from groundtruth.core.validation import load_labeled, measure
from groundtruth.products.agentprobe.judge import LLMJudge

REPO = Path(__file__).resolve().parents[2]
CORPUS = "validation/agentprobe"

# The four pre-registered arms. `legacy_parser` is the retired pre-2263f9c
# parser and appears in exactly one arm, for exactly one reason: A0 has to
# reproduce a historical number, so it has to run the historical instrument.
ARMS: dict[str, dict[str, Any]] = {
    "A0": {
        "decode_format": "json",
        "prompt_shape": "array",
        "legacy_parser": True,
        "purpose": "instrument faithfulness — reproduce the published number",
    },
    "A1": {
        "decode_format": "json",
        "prompt_shape": "array",
        "legacy_parser": False,
        "purpose": "isolates confound 2 (the parser)",
    },
    "B": {
        "decode_format": "json",
        "prompt_shape": "object",
        "legacy_parser": False,
        "purpose": "constraint and prompt agree",
    },
    "C": {
        "decode_format": None,
        "prompt_shape": "array",
        "legacy_parser": False,
        "purpose": "prompt as designed, no decode constraint",
    },
}

SUBJECTS = ("llama3.1:8b", "gemma3:4b")

# Published figures under test, from runs/detector-quality-judge-*.json.
PUBLISHED_PRECISION = {"llama3.1:8b": 0.2254, "gemma3:4b": 0.3387}
PUBLISHED_ARTIFACT = {
    "llama3.1:8b": "runs/detector-quality-judge-llama3.1-8b.json",
    "gemma3:4b": "runs/detector-quality-judge-gemma3-4b.json",
}
P1_TOLERANCE = 0.03


def _slug(model: str) -> str:
    return model.replace(":", "-").replace("/", "-")


def _cell_paths(out: Path, arm: str, model: str) -> tuple[Path, Path]:
    stem = f"{arm}--{_slug(model)}.json"
    return out / "metrics" / stem, out / "replies" / stem


def run_cell(arm: str, model: str, out: Path, force: bool) -> dict[str, Any]:
    """Measure one (arm, subject) cell, writing both artifacts before returning.

    The write happens here rather than at the end of the sweep so a crash in a
    later cell cannot destroy an earlier cell's ~5 minutes of model calls.
    """
    metrics_path, replies_path = _cell_paths(out, arm, model)
    if metrics_path.exists() and replies_path.exists() and not force:
        print(f"[{arm} {model}] cached -> {metrics_path.name}", flush=True)
        return json.loads(metrics_path.read_text())

    config = ARMS[arm]
    judge = LLMJudge(
        model,
        prompt_shape=config["prompt_shape"],
        decode_format=config["decode_format"],
        legacy_parser=config["legacy_parser"],
    )
    items = load_labeled(REPO / CORPUS)
    t0 = time.time()
    report = measure(items, [judge]).to_dict()
    elapsed = round(time.time() - t0, 1)

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(report, indent=2))
    replies_path.parent.mkdir(parents=True, exist_ok=True)
    replies_path.write_text(
        json.dumps(
            {
                "arm": arm,
                "subject": model,
                "config": {k: v for k, v in config.items() if k != "purpose"},
                "system_prompt": judge.system,
                "parse_failures": judge.parse_failures,
                "n_calls": len(judge.calls),
                "wall_seconds": elapsed,
                "calls": [c.to_dict() for c in judge.calls],
            },
            indent=2,
        )
    )

    micro = report["micro"]
    print(
        f"[{arm} {model}] P={micro['precision']} R={micro['recall']} "
        f"F1={micro['f1']} tp/fp/fn={micro['tp']}/{micro['fp']}/{micro['fn']} "
        f"parse_fail={judge.parse_failures}/{len(judge.calls)} {elapsed}s",
        flush=True,
    )
    return report


def check_p1(a0_reports: dict[str, dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
    """P1 — A0 reproduces published precision within +/-0.03 for both subjects."""
    rows = []
    for model in SUBJECTS:
        measured = a0_reports[model]["micro"]["precision"]
        published = PUBLISHED_PRECISION[model]
        delta = round(measured - published, 4)
        rows.append(
            {
                "subject": model,
                "published_precision": published,
                "measured_precision": measured,
                "delta": delta,
                "within_tolerance": abs(delta) <= P1_TOLERANCE,
            }
        )
    return all(r["within_tolerance"] for r in rows), rows


def summarize(out: Path) -> dict[str, Any]:
    """Machine-readable roll-up of every cell present on disk."""
    cells = []
    for arm in ARMS:
        for model in SUBJECTS:
            metrics_path, replies_path = _cell_paths(out, arm, model)
            if not metrics_path.exists():
                continue
            report = json.loads(metrics_path.read_text())
            replies = json.loads(replies_path.read_text()) if replies_path.exists() else {}
            micro = report["micro"]
            cells.append(
                {
                    "arm": arm,
                    "subject": model,
                    "config": {k: v for k, v in ARMS[arm].items() if k != "purpose"},
                    "n_items": report["n_items"],
                    "precision": micro["precision"],
                    "recall": micro["recall"],
                    "f1": micro["f1"],
                    "tp": micro["tp"],
                    "fp": micro["fp"],
                    "fn": micro["fn"],
                    "parse_failures": replies.get("parse_failures"),
                    "n_calls": replies.get("n_calls"),
                    "wall_seconds": replies.get("wall_seconds"),
                    "fp_by_category": {
                        c: m["fp"] for c, m in report["per_category"].items()
                    },
                }
            )
    return {
        "experiment": "judge-rerun",
        "preregistration": "docs/specs/2026-08-02-judge-rerun-preregistration.md",
        "predictions_commit": "3d00783",
        "protocol": {
            "temperature": 0,
            "seed": 42,
            "corpus": CORPUS,
            "n_items": 68,
            "date": time.strftime("%Y-%m-%d"),
        },
        "arms": {a: dict(c) for a, c in ARMS.items()},
        "published_under_test": {
            m: {"precision": PUBLISHED_PRECISION[m], "artifact": PUBLISHED_ARTIFACT[m]}
            for m in SUBJECTS
        },
        "cells": cells,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out", default=f"runs/experiments/judge-rerun-{time.strftime('%Y-%m-%d')}"
    )
    parser.add_argument("--arms", nargs="*", default=list(ARMS), choices=list(ARMS))
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--skip-gate",
        action="store_true",
        help="run the requested arms without enforcing the P1 stop rule "
        "(for re-summarising an already-gated run only)",
    )
    args = parser.parse_args()

    out = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    requested = [a for a in ARMS if a in args.arms]

    # The gate runs first and alone. Nothing downstream is worth measuring
    # until the instrument reproduces a number we already know.
    if "A0" in requested:
        a0 = {m: run_cell("A0", m, out, args.force) for m in SUBJECTS}
        holds, rows = check_p1(a0)
        (out / "p1-gate.json").write_text(
            json.dumps(
                {"tolerance": P1_TOLERANCE, "holds": holds, "subjects": rows}, indent=2
            )
        )
        print("\n=== P1 GATE ===", flush=True)
        for r in rows:
            print(
                f"  {r['subject']:14s} published {r['published_precision']}  "
                f"measured {r['measured_precision']}  delta {r['delta']:+.4f}  "
                f"{'OK' if r['within_tolerance'] else 'OUT OF TOLERANCE'}",
                flush=True,
            )
        print(f"  P1 {'CONFIRMED' if holds else 'FALSIFIED'}\n", flush=True)
        if not holds and not args.skip_gate:
            (out / "summary.json").write_text(json.dumps(summarize(out), indent=2))
            print(
                "P1 failed — protocol stops the experiment here and reports it "
                "inconclusive. No further arm is run.",
                flush=True,
            )
            return 1

    for arm in [a for a in requested if a != "A0"]:
        for model in SUBJECTS:
            run_cell(arm, model, out, args.force)

    (out / "summary.json").write_text(json.dumps(summarize(out), indent=2))
    print(
        f"DONE in {round(time.time() - t_start, 1)}s -> {out}/summary.json", flush=True
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
