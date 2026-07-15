"""Evidence Model — the ontology, admitted explicitly.

One primitive (EvidenceNode) with typed kinds; plain frozen dataclasses; no
I/O anywhere in this module. The loader resolves every environmental fact
(file existence, git validity, versions) into node attrs at load time, so
all downstream layers are pure functions of the model.

Current consumers: meta.loader, meta.graph, meta.contracts, meta.manifest,
meta.assurance. Future consumers: JudgeKit / PlannerBench registers.
"""
from __future__ import annotations

from dataclasses import dataclass, field

KINDS = ("claim", "threat", "artifact", "experiment", "version")


@dataclass(frozen=True)
class Provenance:
    source: str
    location: str = ""


@dataclass(frozen=True)
class EvidenceNode:
    id: str
    kind: str
    provenance: Provenance
    attrs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown kind: {self.kind!r} (expected one of {KINDS})")


@dataclass(frozen=True)
class Edge:
    src: str
    kind: str
    dst: str
