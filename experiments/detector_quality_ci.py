"""Bootstrap confidence intervals for the published detector-quality numbers.

Deterministic (seed 42, 10k resamples). Item-level resampling of the 68-item
labeled corpus; detector verdicts are deterministic per item, so the per-item
confusion contributions are computed once and resampled.

This is the one statistical characterization the corpus size honestly
supports: it answers "how uncertain are the published micro P/R given 68
items?" — nothing more. Per-scenario benchmark results (n=8) get no interval
because none would be meaningful; they are published as existence proofs.

Run from the repo root:
    ./.venv/bin/python experiments/detector_quality_ci.py
"""
from __future__ import annotations

import random

from groundtruth.core.validation import load_labeled
from groundtruth.products.agentprobe.detectors import (
    GoalDrift,
    InjectionCompliance,
    NonCompletion,
    OverRefusal,
    SecretLeak,
    UnsafeToolCall,
)

DETECTORS = [
    UnsafeToolCall(),
    InjectionCompliance(),
    SecretLeak(),
    GoalDrift(),
    OverRefusal(),
    NonCompletion(),
]
RESAMPLES = 10_000
SEED = 42


def main() -> None:
    items = load_labeled("validation/agentprobe")
    per_item: list[tuple[int, int, int]] = []
    for it in items:
        detected = {f.category for d in DETECTORS for f in d.detect(it.case, it.trace)}
        per_item.append(
            (len(detected & it.labels), len(detected - it.labels), len(it.labels - detected))
        )

    tp = sum(x[0] for x in per_item)
    fp = sum(x[1] for x in per_item)
    fn = sum(x[2] for x in per_item)
    print(f"items: {len(per_item)}   point micro: P {tp/(tp+fp):.4f}  R {tp/(tp+fn):.4f}")

    rng = random.Random(SEED)
    n = len(per_item)
    ps: list[float] = []
    rs: list[float] = []
    for _ in range(RESAMPLES):
        btp = bfp = bfn = 0
        for _ in range(n):
            a, b, c = per_item[rng.randrange(n)]
            btp += a
            bfp += b
            bfn += c
        ps.append(btp / (btp + bfp) if btp + bfp else 1.0)
        rs.append(btp / (btp + bfn) if btp + bfn else 1.0)
    ps.sort()
    rs.sort()
    lo, hi = int(0.025 * RESAMPLES), int(0.975 * RESAMPLES)
    print(f"bootstrap 95% CI ({RESAMPLES} resamples, seed {SEED}):")
    print(f"  precision: [{ps[lo]:.4f}, {ps[hi]:.4f}]")
    print(f"  recall:    [{rs[lo]:.4f}, {rs[hi]:.4f}]")


if __name__ == "__main__":
    main()
