"""Evidence Loader — the ONE concrete adapter: YAML registers + filesystem +
git facts -> Evidence Model nodes.

All environmental resolution happens here (file existence, glob matches,
metric-source values, script paths, git commit validity, version strings) so
that graph/contracts/manifest/assurance stay pure. Deliberately no abstract
base class, no plugin system, no loader registry (ADR-0006 / ARB guardrail):
room for future consumers lives in the register FORMATS, not in interfaces.

Current consumers: `groundtruth audit` CLI. Future consumers: JudgeKit /
PlannerBench registers, external evaluations emitting the same formats.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml

from .model import EvidenceNode, Provenance


class RegisterError(Exception):
    """A register is missing or malformed. CLI maps this to exit code 2."""


_PYPROJECT_VERSION = re.compile(r'^version\s*=\s*"([^"]+)"', re.M)
_README_VERSION = re.compile(r"\*\*v(\d+\.\d+) — shipping\*\*")
_PROSE_THREAT_ID = re.compile(r"^\|\s*([IEKS]\d+|T\d+)\s*\|", re.M)


def probe_git_facts(
    root: Path, commits: list[str], ancestry: list[tuple[str, str]] = ()
) -> dict:
    facts: dict = {"__ancestry__": {}}
    for sha in commits:
        proc = subprocess.run(
            ["git", "cat-file", "-t", sha], cwd=root, capture_output=True, text=True
        )
        facts[sha] = {"exists": proc.returncode == 0 and proc.stdout.strip() == "commit"}
    for a, b in ancestry:
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", a, b], cwd=root, capture_output=True
        )
        facts["__ancestry__"][(a, b)] = proc.returncode == 0
    return facts


def _read_register(path: Path, key: str) -> tuple[dict, list[dict]]:
    if not path.exists():
        raise RegisterError(f"register not found: {path.name} (looked at {path})")
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        raise RegisterError(f"{path.name}: expected a mapping with a '{key}' list")
    for entry in data[key]:
        if not isinstance(entry, dict) or "id" not in entry:
            raise RegisterError(f"{path.name}: every {key} entry needs an 'id'")
    return data, data[key]


def _artifact_node(root: Path, rel: str, source: str) -> EvidenceNode:
    is_glob = any(ch in rel for ch in "*?[")
    if is_glob:
        matches = len(sorted(root.glob(rel)))
        attrs = {"exists": matches > 0, "glob": True, "matches": matches}
    else:
        exists = (root / rel).exists()
        attrs = {"exists": exists, "glob": False, "matches": int(exists)}
    return EvidenceNode(
        id=f"artifact:{rel}", kind="artifact",
        provenance=Provenance(source=source, location=rel), attrs=attrs,
    )


def _resolve_metrics(root: Path, metrics: list[dict]) -> list[dict]:
    resolved = []
    for m in metrics:
        actual = None
        src = root / m["source"]
        if src.exists():
            try:
                value: object = json.loads(src.read_text())
                for part in m["path"].split("."):
                    value = value[part]  # type: ignore[index]
                actual = value
            except (json.JSONDecodeError, KeyError, TypeError):
                actual = None
        resolved.append({**m, "actual": actual})
    return resolved


def _script_paths(root: Path, command: str) -> dict[str, bool]:
    paths: dict[str, bool] = {}
    for token in command.split():
        token = token.rstrip(",.);")
        if "/" not in token or token.startswith("--") or token.startswith("./.venv"):
            continue
        paths[token] = (root / token).exists()
    return paths


def load_evidence(
    root: Path,
    claims_path: Path | None = None,
    threats_path: Path | None = None,
    git_facts: dict | None = None,
) -> list[EvidenceNode]:
    root = Path(root)
    claims_path = claims_path or root / "docs/claims.yaml"
    threats_path = threats_path or root / "docs/threats.yaml"
    claims_doc, claims = _read_register(claims_path, "claims")
    _, threats = _read_register(threats_path, "threats")

    harness_commit = str(claims_doc.get("harness_commit", ""))
    prereg_pairs = [
        (c["preregistration"]["predictions_commit"], c["preregistration"]["results_commit"])
        for c in claims
        if isinstance(c.get("preregistration"), dict)
    ]
    if git_facts is None:
        commits = [harness_commit] + [sha for pair in prereg_pairs for sha in pair]
        git_facts = probe_git_facts(root, [c for c in commits if c], prereg_pairs)

    nodes: dict[str, EvidenceNode] = {}

    def add(node: EvidenceNode) -> None:
        nodes.setdefault(node.id, node)

    for c in claims:
        attrs = {k: v for k, v in c.items() if k not in ("id", "evidence", "metrics")}
        attrs["evidence_paths"] = []
        attrs["external_evidence"] = []
        for entry in c.get("evidence", []):
            if isinstance(entry, dict):
                attrs["external_evidence"].append(entry)
            else:
                attrs["evidence_paths"].append(str(entry))
                add(_artifact_node(root, str(entry), source=claims_path.name))
        if c.get("metrics"):
            attrs["metrics_resolved"] = _resolve_metrics(root, c["metrics"])
            for m in c["metrics"]:
                add(_artifact_node(root, m["source"], source=claims_path.name))
        if isinstance(c.get("preregistration"), dict):
            pair = (
                c["preregistration"]["predictions_commit"],
                c["preregistration"]["results_commit"],
            )
            attrs["preregistration_verified"] = bool(git_facts["__ancestry__"].get(pair, False))
        add(EvidenceNode(
            id=f"claim:{c['id']}", kind="claim",
            provenance=Provenance(source=claims_path.name, location=str(c["id"])),
            attrs=attrs,
        ))
        if c.get("reproduce"):
            add(EvidenceNode(
                id=f"experiment:{c['id']}", kind="experiment",
                provenance=Provenance(source=claims_path.name, location=str(c["id"])),
                attrs={
                    "command": c["reproduce"],
                    "script_paths": _script_paths(root, c["reproduce"]),
                },
            ))

    for t in threats:
        attrs = {k: v for k, v in t.items() if k not in ("id", "evidence")}
        attrs["evidence_paths"] = [str(e) for e in t.get("evidence", [])]
        for rel in attrs["evidence_paths"]:
            add(_artifact_node(root, rel, source=threats_path.name))
        add(EvidenceNode(
            id=f"threat:{t['id']}", kind="threat",
            provenance=Provenance(source=threats_path.name, location=str(t["id"])),
            attrs=attrs,
        ))

    pyproject = (root / "pyproject.toml").read_text() if (root / "pyproject.toml").exists() else ""
    readme = (root / "README.md").read_text() if (root / "README.md").exists() else ""
    pv = _PYPROJECT_VERSION.search(pyproject)
    rv = _README_VERSION.search(readme)
    add(EvidenceNode(
        id=f"version:{harness_commit}", kind="version",
        provenance=Provenance(source=claims_path.name, location="harness_commit"),
        attrs={
            "exists_in_git": bool(git_facts.get(harness_commit, {}).get("exists", False)),
            "pyproject_version": pv.group(1) if pv else None,
            "readme_version": rv.group(1) if rv else None,
        },
    ))

    prose = root / "docs/THREATS_TO_VALIDITY.md"
    if prose.exists():
        add(EvidenceNode(
            id="artifact:docs/THREATS_TO_VALIDITY.md", kind="artifact",
            provenance=Provenance(source="docs/THREATS_TO_VALIDITY.md"),
            attrs={
                "exists": True, "glob": False, "matches": 1,
                "prose_threat_ids": _PROSE_THREAT_ID.findall(prose.read_text()),
            },
        ))
    return list(nodes.values())
