"""Evidence Graph — the primary internal representation of the engine.

Built from Evidence Model nodes only (never raw YAML). Pure: no I/O. The
provenance question the graph answers is "why do you claim X?" — follow
edges from a claim to its artifacts, experiments, threats, and version.

Current consumers: meta.contracts, meta.manifest, meta.assurance.
Future consumers: JudgeKit / PlannerBench registers via the same loader.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import Edge, EvidenceNode


@dataclass(frozen=True)
class EvidenceGraph:
    nodes: dict[str, EvidenceNode]
    edges: tuple[Edge, ...]

    def node(self, node_id: str) -> EvidenceNode | None:
        return self.nodes.get(node_id)

    def out(self, src_id: str, kind: str | None = None) -> list[Edge]:
        return [e for e in self.edges if e.src == src_id and (kind is None or e.kind == kind)]

    def by_kind(self, kind: str) -> list[EvidenceNode]:
        return sorted((n for n in self.nodes.values() if n.kind == kind), key=lambda n: n.id)


def build_graph(nodes: list[EvidenceNode]) -> EvidenceGraph:
    index = {n.id: n for n in nodes}
    edges: list[Edge] = []
    versions = [n.id for n in nodes if n.kind == "version"]
    for n in nodes:
        if n.kind == "claim":
            for rel in n.attrs.get("evidence_paths", []):
                edges.append(Edge(n.id, "supported_by", f"artifact:{rel}"))
            for m in n.attrs.get("metrics_resolved", []):
                edges.append(Edge(n.id, "supported_by", f"artifact:{m['source']}"))
            for tid in n.attrs.get("threat_refs", []):
                edges.append(Edge(n.id, "threatened_by", f"threat:{tid}"))
            claim_id = n.id.removeprefix("claim:")
            if f"experiment:{claim_id}" in index:
                edges.append(Edge(n.id, "reproduced_by", f"experiment:{claim_id}"))
            for vid in versions:
                edges.append(Edge(n.id, "measured_at", vid))
        elif n.kind == "threat":
            for rel in n.attrs.get("evidence_paths", []):
                edges.append(Edge(n.id, "mitigated_by", f"artifact:{rel}"))
    deduped = sorted(set(edges), key=lambda e: (e.src, e.kind, e.dst))
    return EvidenceGraph(nodes=index, edges=tuple(deduped))
