"""Evaluation Contracts — declarative invariants over the Evidence Graph.

Pure functions of the graph (the loader already resolved every environmental
fact into node attrs). Findings are explanatory objects, never scores —
deliberate symmetry with the detector philosophy (ADR-0002). CT10
(byte-determinism of audit outputs) cannot be a graph invariant; it is
enforced by tests/test_meta_manifest.py and tests/test_meta_assurance.py and
documented here so the manifest can state the full contract set.

Current consumers: meta.manifest, meta.assurance, `groundtruth audit` CLI.
Future consumers: any evaluation emitting the register formats.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .graph import EvidenceGraph

VOCAB = ("fact", "supported_observation", "working_hypothesis", "speculation", "retracted")
STATUSES = ("open", "mitigated", "resolved")
CONFIDENCES = ("high", "medium", "low")


@dataclass(frozen=True)
class Finding:
    contract_id: str
    node_id: str
    summary: str


@dataclass(frozen=True)
class Contract:
    id: str
    invariant: str
    check: Callable[[EvidenceGraph], list[Finding]]


def _ct1(g: EvidenceGraph) -> list[Finding]:
    out = []
    for c in g.by_kind("claim"):
        for rel in c.attrs.get("evidence_paths", []):
            art = g.node(f"artifact:{rel}")
            if art is None or not art.attrs.get("exists", False):
                out.append(Finding("CT1", c.id, f"evidence does not resolve in-repo: {rel}"))
        for ext in c.attrs.get("external_evidence", []):
            if not ext.get("why"):
                out.append(Finding("CT1", c.id, "external evidence lacks a 'why' justification"))
    return out


def _ct2(g: EvidenceGraph) -> list[Finding]:
    out = []
    for c in g.by_kind("claim"):
        if c.attrs.get("classification") == "retracted":
            continue
        if not c.attrs.get("falsification"):
            out.append(Finding("CT2", c.id, "no falsification condition declared"))
        if not c.attrs.get("scope"):
            out.append(Finding("CT2", c.id, "no scope sentence declared"))
    return out


def _ct3(g: EvidenceGraph) -> list[Finding]:
    out = []
    for c in g.by_kind("claim"):
        cls = c.attrs.get("classification")
        if cls not in VOCAB:
            out.append(Finding("CT3", c.id, f"classification {cls!r} not in vocabulary"))
            continue
        if cls == "fact":
            if not c.attrs.get("evidence_paths"):
                out.append(Finding("CT3", c.id, "fact has no in-repo evidence path"))
            if not c.attrs.get("reproduce"):
                out.append(Finding("CT3", c.id, "fact has no reproduce command"))
    for e in g.by_kind("experiment"):
        for path, exists in e.attrs.get("script_paths", {}).items():
            if not exists:
                out.append(Finding("CT3", e.id, f"reproduce references missing path: {path}"))
    return out


def _ct4(g: EvidenceGraph) -> list[Finding]:
    out = []
    for c in g.by_kind("claim"):
        cid = c.id.removeprefix("claim:")
        for tid in c.attrs.get("threat_refs", []):
            t = g.node(f"threat:{tid}")
            if t is None:
                out.append(Finding("CT4", c.id, f"threat_ref does not resolve: {tid}"))
            elif cid not in t.attrs.get("claim_refs", []):
                out.append(Finding("CT4", c.id, f"one-way reference: {tid} does not list {cid}"))
    for t in g.by_kind("threat"):
        tid = t.id.removeprefix("threat:")
        for cid in t.attrs.get("claim_refs", []):
            c = g.node(f"claim:{cid}")
            if c is None:
                out.append(Finding("CT4", t.id, f"claim_ref does not resolve: {cid}"))
            elif tid not in c.attrs.get("threat_refs", []):
                out.append(Finding("CT4", t.id, f"one-way reference: {cid} does not list {tid}"))
    return out


def _ct5(g: EvidenceGraph) -> list[Finding]:
    out = []
    for c in g.by_kind("claim"):
        for m in c.attrs.get("metrics_resolved", []):
            if m["actual"] != m["value"]:
                out.append(Finding(
                    "CT5", c.id,
                    f"metric {m['name']}: claim says {m['value']}, "
                    f"{m['source']}:{m['path']} says {m['actual']}"))
    return out


def _ct6(g: EvidenceGraph) -> list[Finding]:
    out = []
    for v in g.by_kind("version"):
        if not v.attrs.get("exists_in_git"):
            out.append(Finding("CT6", v.id, "harness_commit not found in git history"))
        pv, rv = v.attrs.get("pyproject_version"), v.attrs.get("readme_version")
        if not pv or not rv:
            out.append(Finding("CT6", v.id, f"version string missing (pyproject={pv}, readme={rv})"))
        elif not (pv == rv or pv.startswith(rv + ".")):
            out.append(Finding("CT6", v.id, f"version drift: pyproject {pv} vs README v{rv}"))
    return out


def _ct7(g: EvidenceGraph) -> list[Finding]:
    out = []
    for t in g.by_kind("threat"):
        if t.attrs.get("status") not in STATUSES:
            out.append(Finding("CT7", t.id, f"status {t.attrs.get('status')!r} not in {STATUSES}"))
        if not t.attrs.get("mitigation"):
            out.append(Finding("CT7", t.id, "no mitigation declared"))
        if not t.attrs.get("future_experiment"):
            out.append(Finding("CT7", t.id, "no future experiment declared"))
        if t.attrs.get("status") == "resolved":
            resolved_ok = False
            for rel in t.attrs.get("evidence_paths", []):
                art = g.node(f"artifact:{rel}")
                if art is not None and art.attrs.get("exists"):
                    resolved_ok = True
            if not resolved_ok:
                out.append(Finding("CT7", t.id, "resolved status requires existing evidence"))
    return out


def _ct8(g: EvidenceGraph) -> list[Finding]:
    prose = g.node("artifact:docs/THREATS_TO_VALIDITY.md")
    if prose is None:
        return [Finding("CT8", "artifact:docs/THREATS_TO_VALIDITY.md", "prose threat doc missing")]
    prose_ids = set(prose.attrs.get("prose_threat_ids", []))
    register_ids = {t.id.removeprefix("threat:") for t in g.by_kind("threat")}
    out = []
    for missing in sorted(prose_ids - register_ids):
        out.append(Finding("CT8", f"threat:{missing}", "in prose doc but not in threats.yaml"))
    for missing in sorted(register_ids - prose_ids):
        out.append(Finding("CT8", f"threat:{missing}", "in threats.yaml but not in prose doc"))
    return out


def _ct9(g: EvidenceGraph) -> list[Finding]:
    out = []
    for c in g.by_kind("claim"):
        if c.attrs.get("confidence") not in CONFIDENCES:
            out.append(Finding("CT9", c.id, f"confidence {c.attrs.get('confidence')!r} invalid"))
        if c.attrs.get("classification") in ("supported_observation", "working_hypothesis"):
            if not c.attrs.get("confounds_remaining"):
                out.append(Finding("CT9", c.id, "non-fact names no remaining confound to resolve"))
    return out


CONTRACTS: tuple[Contract, ...] = (
    Contract("CT1", "every claim's evidence resolves in-repo or is marked external with why", _ct1),
    Contract("CT2", "every non-retracted claim declares falsification and scope", _ct2),
    Contract("CT3", "classification in vocabulary; facts have evidence + working reproduce", _ct3),
    Contract("CT4", "claim<->threat references are bidirectional and resolve", _ct4),
    Contract("CT5", "every quoted metric matches its source artifact", _ct5),
    Contract("CT6", "harness commit exists; pyproject/README/manifest versions agree", _ct6),
    Contract("CT7", "threats carry mitigation + future experiment; resolved needs evidence", _ct7),
    Contract("CT8", "prose and register threat ID sets are identical", _ct8),
    Contract("CT9", "claims carry confidence; non-facts name their remaining confound", _ct9),
)

CONTRACTS_DOC: dict[str, str] = {c.id: c.invariant for c in CONTRACTS}
CONTRACTS_DOC["CT10"] = (
    "audit outputs are byte-identical across runs at the same commit "
    "(enforced by tests/test_meta_manifest.py and tests/test_meta_assurance.py)"
)


def run_contracts(graph: EvidenceGraph) -> list[Finding]:
    findings: list[Finding] = []
    for contract in CONTRACTS:
        findings.extend(contract.check(graph))
    return sorted(findings, key=lambda f: (f.contract_id, f.node_id, f.summary))
