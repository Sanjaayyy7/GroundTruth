"""MiniJudge — a deliberately minimal negation-keyword verdict judge.

Reads data/labeled.json, predicts `refute` for any statement containing a
negation token and `support` otherwise, and writes the agreement measurement
to runs/agreement.json. Deterministic by construction: no randomness, no
timestamps, sorted keys. Stdlib only.

MiniJudge exists solely as the second consumer for Groundtruth's
Meta-Evaluation Engine (v0.7 external validation); it is not a product.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEGATION = re.compile(r"\b(not|no|never|cannot)\b", re.IGNORECASE)


def predict(statement: str) -> str:
    return "refute" if NEGATION.search(statement) else "support"


def measure() -> dict:
    data = json.loads((ROOT / "data/labeled.json").read_text())
    confusion = {"support_as_support": 0, "support_as_refute": 0,
                 "refute_as_refute": 0, "refute_as_support": 0}
    errors = []
    for item in data["items"]:
        predicted = predict(item["statement"])
        confusion[f"{item['reference']}_as_{predicted}"] += 1
        if predicted != item["reference"]:
            errors.append(item["id"])
    correct = confusion["support_as_support"] + confusion["refute_as_refute"]
    return {
        "schema_version": 1,
        "n_items": len(data["items"]),
        "accuracy": correct / len(data["items"]),
        "confusion": confusion,
        "errors": sorted(errors),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "runs/agreement.json"))
    args = parser.parse_args()

    report = measure()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"agreement written: {out} (accuracy {report['accuracy']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
