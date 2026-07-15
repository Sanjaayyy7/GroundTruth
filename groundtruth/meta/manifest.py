"""Quality Manifest — assessment product 1: answers "what evidence exists?"

Sibling of meta.assurance (which answers "what conclusions are justified?");
neither imports the other (ARB Issue 2). Pure over (graph, findings);
rendering is byte-deterministic — sorted keys, no wall-clock timestamps, the
git commit is the time anchor. No composite score, deliberately.

Dimension coverage is register-driven: claims and threats tag themselves
with `dimensions:` entries; this module contains no evaluation-specific
node ids (ARB modification 1 — no Groundtruth literals in meta/).

Current consumers: `groundtruth audit` CLI, CI. Future consumers: JudgeKit /
PlannerBench releases publishing the same manifest format.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict

from .contracts import CONTRACTS_DOC, Finding
from .graph import EvidenceGraph

DIMENSIONS = (
    "determinism", "reproducibility", "detector_quality", "label_quality",
    "dataset_discrimination", "threat_coverage", "statistical_support",
    "claim_traceability", "version_stability", "experimental_rigor",
)


def _tagged(graph: EvidenceGraph, dimension: str) -> list:
    nodes = graph.by_kind("claim") + graph.by_kind("threat")
    return [n for n in nodes if dimension in n.attrs.get("dimensions", [])]


def _node_summary(node) -> dict:
    summary: dict = {"id": node.id}
    for key in ("classification", "confidence", "status"):
        if key in node.attrs:
            summary[key] = node.attrs[key]
    if node.attrs.get("ci_95"):
        summary["ci_95"] = node.attrs["ci_95"]
    if node.attrs.get("metrics_resolved"):
        summary["metrics"] = [
            {"name": m["name"], "value": m["value"], "actual": m["actual"], "source": m["source"]}
            for m in node.attrs["metrics_resolved"]
        ]
    if node.attrs.get("attrs"):
        summary["attrs"] = node.attrs["attrs"]
    return summary


def _tag_dimension(graph: EvidenceGraph, dimension: str) -> dict:
    tagged = _tagged(graph, dimension)
    if not tagged:
        return {"status": "gap", "value": None,
                "note": "no register entry tags this dimension"}
    machine = any(
        n.attrs.get("metrics_resolved") or n.attrs.get("ci_95") or n.attrs.get("attrs")
        for n in tagged
    )
    return {"status": "machine" if machine else "documented",
            "value": [_node_summary(n) for n in tagged]}


def build_manifest(
    graph: EvidenceGraph, findings: list[Finding], evaluation_name: str = "groundtruth"
) -> dict:
    claims = graph.by_kind("claim")
    threats = graph.by_kind("threat")
    versions = graph.by_kind("version")
    version_node = versions[0] if versions else None

    flagged = {f.node_id for f in findings if f.contract_id in ("CT1", "CT2")}
    traced = sum(1 for c in claims if c.id not in flagged)

    dimensions = {
        "D01_determinism": _tag_dimension(graph, "determinism"),
        "D02_reproducibility": _tag_dimension(graph, "reproducibility"),
        "D03_detector_quality": _tag_dimension(graph, "detector_quality"),
        "D04_label_quality": _tag_dimension(graph, "label_quality"),
        "D05_dataset_discrimination": _tag_dimension(graph, "dataset_discrimination"),
        "D06_threat_coverage": {
            "status": "machine",
            "value": {
                "by_status": dict(sorted(Counter(t.attrs.get("status") for t in threats).items())),
                "by_category": dict(sorted(Counter(t.attrs.get("category") for t in threats).items())),
            },
        },
        "D07_statistical_support": _tag_dimension(graph, "statistical_support"),
        "D08_claim_traceability": {
            "status": "machine",
            "value": {"traced": traced, "total": len(claims)},
        },
        "D09_version_stability": {
            "status": "machine",
            "value": dict(version_node.attrs) if version_node else None,
        },
        "D10_experimental_rigor": {
            "status": "machine",
            "value": [c.id for c in claims if c.attrs.get("preregistration_verified")],
        },
    }

    return {
        "manifest_schema_version": 1,
        "evaluation": {
            "name": evaluation_name,
            "version": version_node.attrs.get("pyproject_version") if version_node else None,
            "harness_commit": version_node.id.removeprefix("version:") if version_node else None,
        },
        "registers": {
            "claims": {
                "total": len(claims),
                "by_classification": dict(sorted(
                    Counter(c.attrs.get("classification") for c in claims).items())),
            },
            "threats": {
                "total": len(threats),
                "by_status": dict(sorted(Counter(t.attrs.get("status") for t in threats).items())),
                "by_category": dict(sorted(Counter(t.attrs.get("category") for t in threats).items())),
            },
        },
        "dimensions": dimensions,
        "contracts": {
            "definitions": dict(CONTRACTS_DOC),
            "findings": [asdict(f) for f in findings],
            "holds": not findings,
        },
        "graph": {
            "nodes": len(graph.nodes),
            "edges": len(graph.edges),
            "nodes_by_kind": dict(sorted(Counter(n.kind for n in graph.nodes.values()).items())),
        },
        "unresolved_threats": [
            t.id.removeprefix("threat:") for t in threats if t.attrs.get("status") != "resolved"
        ],
        "no_composite_score": (
            "deliberate — a scalar would exceed the evidence (see docs/EVALUATION_QUALITY.md)"
        ),
    }


def render_manifest(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"
