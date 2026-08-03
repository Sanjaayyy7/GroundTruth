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


CHECKS: tuple[str, ...] = tuple(f"RC{n}" for n in range(1, 10))


def trigger_ledger(active: tuple, exempted: tuple, version: str) -> dict:
    """Which checks reported, for one version. Retirement triggers stay in the
    Constitution: restating one in code is a second place for it to drift, the
    failure this layer exists to prevent. The series is recovered by reading
    this artifact across git history, not by a second time anchor.

    Silent is NOT unnecessary. RC1 and RC6 fire locally and are fixed before
    anything reaches CI — debt #18 accepts that friction as the enforcement
    mechanism — so a working deterrent and a useless check look identical here.
    That ambiguity is a defect in the triggers' wording, surfaced by trying to
    evaluate them, and the field is named `silent` so it cannot be misquoted."""
    fired = {f.check_id for f in active} | {f.check_id for f in exempted}
    return {
        "version": version,
        "fired": sorted(c for c in CHECKS if c in fired),
        "silent": sorted(c for c in CHECKS if c not in fired),
        "note": "silent here, not unnecessary: a check fixed pre-push never reaches this run",
    }


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
        "## Trigger ledger",
        "",
        "Silent means silent here, not unnecessary: a check fixed pre-push never",
        "reaches this table (debt #18 accepts that friction deliberately). Each",
        "retirement condition is in the Constitution, not restated here.",
        "",
    ]
    led = inventory.get("trigger_ledger", {})
    lines += [
        f"fired: {', '.join(led.get('fired', [])) or 'none'}",
        f"silent: {', '.join(led.get('silent', [])) or 'none'}",
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
