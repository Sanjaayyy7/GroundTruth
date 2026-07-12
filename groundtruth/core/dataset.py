"""Groundtruth Core — Dataset Store.

A Case is one evaluation instance loaded from YAML. It is generic across products:
for AgentProbe it is an attack scenario, for JudgeKit a battle pair, for
PlannerBench a task. Product-specific fields live untouched in `spec`, so the
core never needs to know what a product's cases contain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_RESERVED = {"id", "product", "suite", "description"}


@dataclass
class Case:
    id: str
    suite: str
    description: str = ""
    spec: dict[str, Any] = field(default_factory=dict)


def load_cases(path: str | Path) -> list[Case]:
    root = Path(path)
    files = sorted(root.glob("*.yaml")) if root.is_dir() else [root]
    cases: list[Case] = []
    for f in files:
        d = yaml.safe_load(f.read_text())
        cases.append(
            Case(
                id=d["id"],
                suite=d.get("product", d.get("suite", "")),
                description=d.get("description", ""),
                spec={k: v for k, v in d.items() if k not in _RESERVED},
            )
        )
    return cases
