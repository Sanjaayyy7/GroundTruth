"""Groundtruth Core — Dataset Store.

A Case is one evaluation instance loaded from YAML. It is generic across products:
for AgentProbe it is an attack scenario, for JudgeKit a battle pair, for
PlannerBench a task. Product-specific fields live untouched in `spec`, so the
core never needs to know what a product's cases contain.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_RESERVED = {"id", "product", "suite", "description"}


class CaseSchemaError(ValueError):
    """A case file violates its product's declared vocabulary."""


@dataclass
class Case:
    id: str
    suite: str
    description: str = ""
    spec: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CaseSchema:
    """The key vocabulary one product's case files may use.

    Labels have been vocabulary-guarded since v0.2 (debt #4) while cases were
    not, which left the *larger* of the two surfaces unguarded. The failure it
    admits is silent rather than loud: a scenario misspelling `completion_tools`
    still loads, still runs, and still scores — it just carries no completion
    contract, so `over_refusal` can never fire on it and the resulting clean
    scorecard is indistinguishable from a real pass.

    The schema is declared by the product and enforced here because core must
    not learn what an AgentProbe scenario contains (ADR-0001 layering, enforced
    by RC5). Type checks are deliberately shallow — presence and container kind,
    not element structure — because a schema that restates the whole format
    becomes a second definition of it, and two definitions drift.
    """

    required: frozenset[str]
    optional: frozenset[str]
    types: Mapping[str, type | tuple[type, ...]] = field(default_factory=dict)

    @property
    def known(self) -> frozenset[str]:
        return self.required | self.optional

    def errors(self, doc: Mapping[str, Any]) -> list[str]:
        """Every violation in `doc`, so one pass names them all.

        Reporting the first and stopping would make fixing an n-error file an
        n-run loop, which is how a guard becomes a thing people route around.
        """
        found = []
        for key in sorted(self.required - set(doc)):
            found.append(f"missing required key '{key}'")
        for key in sorted(set(doc) - self.known):
            found.append(f"unknown key '{key}' — not in the declared vocabulary")
        for key, expected in sorted(self.types.items(), key=lambda kv: kv[0]):
            if key in doc and not isinstance(doc[key], expected):
                names = expected if isinstance(expected, tuple) else (expected,)
                found.append(
                    f"key '{key}' must be {' or '.join(t.__name__ for t in names)}, "
                    f"got {type(doc[key]).__name__}"
                )
        return found


def load_cases(path: str | Path, schema: CaseSchema | None = None) -> list[Case]:
    """Load every case under `path`, optionally checked against `schema`.

    `schema` stays optional so a product can adopt the guard without every
    consumer changing at once, and so core keeps working for a product that has
    not declared a vocabulary yet.
    """
    root = Path(path)
    files = sorted(root.glob("*.yaml")) if root.is_dir() else [root]
    cases: list[Case] = []
    for f in files:
        d = yaml.safe_load(f.read_text())
        if not isinstance(d, dict):
            raise CaseSchemaError(f"{f}: expected a YAML mapping, got {type(d).__name__}")
        if schema is not None:
            problems = schema.errors(d)
            if problems:
                raise CaseSchemaError(f"{f}: " + "; ".join(problems))
        cases.append(
            Case(
                id=d["id"],
                suite=str(d.get("product", d.get("suite", "")) or ""),
                description=d.get("description", ""),
                spec={k: v for k, v in d.items() if k not in _RESERVED},
            )
        )
    return cases
