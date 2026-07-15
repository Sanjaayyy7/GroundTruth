"""Assurance Report — assessment product 2: answers "what conclusions are
justified?" per conclusion, never per repository.

Sibling of meta.manifest; neither imports the other (ARB Issue 2). Pure over
(graph, findings); output is deterministic Markdown. Deliberately no
aggregate verdict, no green/yellow/red, no score — assurance is a statement
about each conclusion's evidence, not a grade for the repo.

Current consumers: `groundtruth audit` CLI. Future consumers: JudgeKit /
PlannerBench releases publishing the same report format.
"""
from __future__ import annotations

from .contracts import Finding
from .graph import EvidenceGraph


def _statement(node) -> str:
    text = str(node.attrs.get("statement", "")).strip().replace("\n", " ")
    return (text[:100] + "…") if len(text) > 100 else text


def render_assurance(graph: EvidenceGraph, findings: list[Finding]) -> str:
    claims = graph.by_kind("claim")
    threats = graph.by_kind("threat")
    versions = graph.by_kind("version")
    commit = versions[0].id.removeprefix("version:") if versions else "unknown"
    flagged = {f.node_id for f in findings}

    lines: list[str] = ["# Assurance Report", "", f"Evaluation evidence @ `{commit}`.", ""]

    lines += ["## Strongly supported", ""]
    strong = [c for c in claims
              if c.attrs.get("classification") == "fact" and c.id not in flagged]
    if strong:
        for c in strong:
            lines.append(f"- **{c.id}** {_statement(c)}")
            for e in graph.out(c.id, kind="supported_by"):
                lines.append(f"  - evidence: `{e.dst.removeprefix('artifact:')}`")
            if c.attrs.get("reproduce"):
                lines.append(f"  - reproduce: `{str(c.attrs['reproduce']).strip()}`")
    else:
        lines.append("- None: no fact currently passes every contract.")
    lines.append("")

    lines += ["## Provisional", ""]
    provisional = [c for c in claims if c.attrs.get("classification")
                   in ("supported_observation", "working_hypothesis")]
    if provisional:
        for c in provisional:
            lines.append(f"- **{c.id}** ({c.attrs.get('classification')}) {_statement(c)}")
            for blocker in c.attrs.get("confounds_remaining", []):
                lines.append(f"  - blocking: {str(blocker).strip()}")
    else:
        lines.append("- None.")
    lines.append("")

    lines += ["## Retracted — kept on the record", ""]
    retracted = [c for c in claims if c.attrs.get("classification") == "retracted"]
    if retracted:
        for c in retracted:
            lines.append(f"- **{c.id}** {_statement(c)}")
            for e in graph.out(c.id, kind="supported_by"):
                lines.append(f"  - record: `{e.dst.removeprefix('artifact:')}`")
    else:
        lines.append("- None.")
    lines.append("")

    lines += ["## Unresolved threats", ""]
    open_threats = [t for t in threats if t.attrs.get("status") != "resolved"]
    if open_threats:
        for category in sorted({t.attrs.get("category", "") for t in open_threats}):
            lines.append(f"### {category}")
            for t in (x for x in open_threats if x.attrs.get("category", "") == category):
                lines.append(f"- **{t.id}** {str(t.attrs.get('threat', '')).strip()}")
                future = str(t.attrs.get("future_experiment", "")).strip().replace("\n", " ")
                if future:
                    lines.append(f"  - next: {future}")
            lines.append("")
    else:
        lines += ["- None.", ""]

    lines += ["## Contract findings", ""]
    if findings:
        lines += ["| contract | node | finding |", "|---|---|---|"]
        for f in findings:
            lines.append(f"| {f.contract_id} | {f.node_id} | {f.summary} |")
    else:
        lines.append("All contracts hold.")
    lines.append("")

    lines += ["## Labeling needs", ""]
    labeled = [t for t in threats if t.attrs.get("attrs", {}).get("annotators") is not None]
    if labeled:
        for t in labeled:
            extra = t.attrs["attrs"]
            lines.append(f"- **{t.id}** annotators: {extra.get('annotators')},"
                         f" kappa: {extra.get('kappa')}")
    else:
        lines.append("- None identified in the registers.")
    lines.append("")

    lines.append("No aggregate verdict: assurance is reported per conclusion, not per repository.")
    lines.append("")
    return "\n".join(lines)
