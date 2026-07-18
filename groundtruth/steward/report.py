"""Steward report — findings + inventory -> committed evidence artifacts.

Byte-deterministic by construction: sorted keys, sorted findings, no
wall-clock timestamps, no absolute paths, LF only (manifest.py
conventions; CT10 parity applies to steward artifacts too).
"""
from __future__ import annotations

import json

from .model import Finding, RepoDeclarations


def render_manifest(inventory: dict) -> str:
    return json.dumps(inventory, indent=2, sort_keys=True) + "\n"


def _finding_line(f: Finding) -> str:
    loc = f"{f.path}:{f.line}" if f.line else f.path
    return f"- [{f.check_id}] {loc} — {f.summary}"


def render_report(
    active: tuple, exempted: tuple, decls: RepoDeclarations, inventory: dict
) -> str:
    lines = [
        "# Repository Steward Report",
        "",
        "Deterministic findings from the Constitution's declarations (schema v1).",
        "Advisory: a finding is resolved by fixing the repository or amending the",
        "Constitution with justification in the same commit (Law 10) — never by",
        "weakening a check.",
        "",
    ]
    if active:
        lines += [f"## Findings ({len(active)})", ""]
        lines += [_finding_line(f) for f in active]
    else:
        lines += ["## Findings", "", "all repository contracts hold"]
    lines += [
        "",
        "## Exemption instrument (R3)",
        "",
        f"active exemptions: {len(decls.exemptions)}",
        f"exempted findings: {len(exempted)}",
    ]
    lines += [
        f"- {e['check']} {e['path']} (since {e['milestone']}) — {e['justification']}"
        for e in decls.exemptions
    ]
    lines += [
        "",
        "review trigger: >=5 active exemptions, or any exemption older than",
        "2 milestones (tribunal R3).",
        "",
        "## Inventory",
        "",
        "| role | files | bytes |",
        "|---|---|---|",
    ]
    lines += [
        f"| {role} | {v['files']} | {v['bytes']} |"
        for role, v in sorted(inventory["roles"].items())
    ]
    total = inventory["total"]
    lines += ["", f"total: {total['files']} files, {total['bytes']} bytes", ""]
    return "\n".join(lines)
