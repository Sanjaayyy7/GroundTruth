"""Groundtruth Core — Validation Engine.

Measures detector quality against hand-labeled traces. A labeled trace pins the
ground truth: the failure categories a perfect detector would report for that
trace. The engine runs real detectors over the labeled set and reports
per-category precision/recall/F1 with an item-level audit trail (which ids were
missed, which were wrongly flagged) — numbers you can defend, not just quote.

Product-agnostic like the rest of the core: AgentProbe validates its safety
detectors today; JudgeKit's agreement detectors and the v0.3 CI regression gate
consume the same report.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .dataset import Case
from .evaluator import Detector
from .scorecard import Failure
from .trace import Trace


@dataclass
class LabeledTrace:
    id: str
    description: str
    case: Case
    trace: Trace
    labels: set[str]


def load_labeled(path: str | Path) -> list[LabeledTrace]:
    root = Path(path)
    files = sorted(root.glob("*.yaml")) if root.is_dir() else [root]
    items: list[LabeledTrace] = []
    for f in files:
        for d in yaml.safe_load_all(f.read_text()):
            if not d:
                continue
            case = Case(
                id=d["id"],
                suite=d.get("suite", ""),
                description=d.get("description", ""),
                spec=d.get("case", {}),
            )
            trace = Trace(subject="labeled", case_id=d["id"])
            for s in d.get("trace", []):
                trace.add(
                    s["kind"],
                    name=s.get("name", ""),
                    content=s.get("content", ""),
                    **s.get("data", {}),
                )
            items.append(
                LabeledTrace(
                    id=d["id"],
                    description=d.get("description", ""),
                    case=case,
                    trace=trace,
                    labels=set(d.get("labels", [])),
                )
            )
    return items


@dataclass
class CategoryMetrics:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    fp_ids: list[str] = field(default_factory=list)
    fn_ids: list[str] = field(default_factory=list)

    @property
    def precision(self) -> float | None:
        return None if self.tp + self.fp == 0 else round(self.tp / (self.tp + self.fp), 4)

    @property
    def recall(self) -> float | None:
        return None if self.tp + self.fn == 0 else round(self.tp / (self.tp + self.fn), 4)

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None or r is None or p + r == 0:
            return None
        return round(2 * p * r / (p + r), 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "fp_ids": self.fp_ids,
            "fn_ids": self.fn_ids,
        }


@dataclass
class ValidationReport:
    n_items: int
    per_category: dict[str, CategoryMetrics]

    @property
    def micro(self) -> CategoryMetrics:
        total = CategoryMetrics()
        for m in self.per_category.values():
            total.tp += m.tp
            total.fp += m.fp
            total.fn += m.fn
        return total

    def to_dict(self) -> dict[str, Any]:
        micro = self.micro
        return {
            "n_items": self.n_items,
            "micro": {
                "tp": micro.tp,
                "fp": micro.fp,
                "fn": micro.fn,
                "precision": micro.precision,
                "recall": micro.recall,
                "f1": micro.f1,
            },
            "per_category": {k: m.to_dict() for k, m in sorted(self.per_category.items())},
        }


def measure(items: list[LabeledTrace], detectors: list[Detector]) -> ValidationReport:
    per_category: dict[str, CategoryMetrics] = {}

    def bucket(category: str) -> CategoryMetrics:
        return per_category.setdefault(category, CategoryMetrics())

    for item in items:
        failures: list[Failure] = []
        for det in detectors:
            failures.extend(det.detect(item.case, item.trace))
        detected = {f.category for f in failures}
        for category in detected | item.labels:
            m = bucket(category)
            if category in detected and category in item.labels:
                m.tp += 1
            elif category in detected:
                m.fp += 1
                m.fp_ids.append(item.id)
            else:
                m.fn += 1
                m.fn_ids.append(item.id)
    return ValidationReport(n_items=len(items), per_category=per_category)
