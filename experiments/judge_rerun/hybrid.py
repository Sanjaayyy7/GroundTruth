"""Hybrid routing — rules as a high-precision first pass, judge on the residue.

DECLARED EXPLORATORY. The pre-registration
(`docs/specs/2026-08-02-judge-rerun-preregistration.md`) spends its one hypothesis
on the decode-constraint confound and explicitly carries no prediction for this.
It is an engineering addition measured with the existing instrument, and it must
never be reported as if it had been pre-registered.

The routing policy is itself a `Detector`: it composes detectors into a detector
without touching `core/`. That is the third load test of the protocol, after the
LLM judge dropped into the identical measurement path and the meta-engine audited
a second consumer with a zero-line diff.

Rationale for the ordering: rules measure at precision 0.9545 and their misses
are published and pinned. A judge that only ever sees traces where every rule
declined is being asked the one question rules cannot answer, and its false
positives can only land on that residue rather than on the whole corpus.

Run:  .venv/bin/python experiments/judge_rerun/hybrid.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from groundtruth.core.dataset import Case  # noqa: E402
from groundtruth.core.scorecard import Failure  # noqa: E402
from groundtruth.core.trace import Trace  # noqa: E402
from groundtruth.core.validation import load_labeled, measure  # noqa: E402
from groundtruth.products.agentprobe.detectors import (  # noqa: E402
    GoalDrift,
    InjectionCompliance,
    NonCompletion,
    OverRefusal,
    SecretLeak,
    UnsafeToolCall,
)
from groundtruth.products.agentprobe.judge import LLMJudge  # noqa: E402

RULES = [
    UnsafeToolCall(),
    InjectionCompliance(),
    SecretLeak(),
    GoalDrift(),
    OverRefusal(),
    NonCompletion(),
]

# Arm B: the best-measured judge configuration from the rerun — decode
# constraint and prompt shape agreeing. Using the confounded configuration here
# would measure the confound a second time instead of the routing policy.
JUDGE_KWARGS = {"prompt_shape": "object", "decode_format": "json"}


class HybridDetector:
    """Rules first; the judge is consulted only when every rule declined."""

    def __init__(self, rules: list, judge: LLMJudge, name: str = "hybrid"):
        self.rules = rules
        self.judge = judge
        self.name = name
        self.judge_calls = 0

    def detect(self, case: Case, trace: Trace) -> list[Failure]:
        failures = [f for d in self.rules for f in d.detect(case, trace)]
        if failures:
            return failures
        self.judge_calls += 1
        return list(self.judge.detect(case, trace))


def main() -> int:
    out = REPO / "runs/experiments/judge-rerun-2026-08-02"
    items = load_labeled(REPO / "validation/agentprobe")

    rules_only = measure(items, RULES).to_dict()

    results = {}
    for model in ("llama3.1:8b", "gemma3:4b"):
        judge = LLMJudge(model, **JUDGE_KWARGS)
        hybrid = HybridDetector(RULES, judge)
        t0 = time.time()
        report = measure(items, [hybrid]).to_dict()
        report["judge_calls"] = hybrid.judge_calls
        report["n_items"] = len(items)
        report["seconds"] = round(time.time() - t0, 1)
        slug = model.replace(":", "-")
        (out / "metrics" / f"HYBRID--{slug}.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        results[model] = report
        m = report["micro"]
        print(
            f"  hybrid+{model:<14} P {m['precision']:<7} R {m['recall']:<7} "
            f"F1 {m['f1']:<7} tp/fp/fn {m['tp']}/{m['fp']}/{m['fn']}  "
            f"judge saw {hybrid.judge_calls}/{len(items)}  {report['seconds']}s",
            flush=True,
        )

    rm = rules_only["micro"]
    print(
        f"  rules alone            P {rm['precision']:<7} R {rm['recall']:<7} "
        f"F1 {rm['f1']:<7} tp/fp/fn {rm['tp']}/{rm['fp']}/{rm['fn']}"
    )
    (out / "hybrid-summary.json").write_text(
        json.dumps(
            {
                "status": "exploratory — not pre-registered",
                "judge_config": JUDGE_KWARGS,
                "rules_only": rules_only["micro"],
                "hybrid": {k: v["micro"] | {"judge_calls": v["judge_calls"]}
                           for k, v in results.items()},
            },
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
