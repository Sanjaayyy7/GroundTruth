# v0.6 Meta-Evaluation Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `groundtruth audit` — constructs an auditable evidence model from evaluation artifacts (claims.yaml, threats.yaml, runs/, git) and derives two sibling deterministic assessments: quality manifest (JSON) and assurance report (Markdown).

**Architecture:** Canonical model from the frozen spec (`docs/specs/2026-07-14-v06-meta-evaluation-design.md`): Evidence Loader (one concrete YAML/filesystem/git adapter) → Evidence Model (EvidenceNode, no I/O) → Evidence Graph (primary representation) → Contracts (pure invariants, findings-not-scores) → {Manifest, Assurance} (siblings, neither imports the other). Import direction enforced: `loader → model ← graph ← contracts ← {manifest, assurance}`.

**Tech Stack:** Python 3.11, stdlib + pyyaml (already a dependency), pytest. No new dependencies.

## Global Constraints

- Import direction: only `loader.py` performs I/O (filesystem, git subprocess); everything downstream is pure over the model/graph.
- Exactly ONE loader. No ABCs, no plugin system, no loader registry, no extension API (ARB guardrail, binding).
- `manifest.py` and `assurance.py` NEVER import each other.
- No composite quality score anywhere. Findings are explanatory objects, never numbers.
- Deterministic outputs: `json.dumps(..., indent=2, sort_keys=True)` + trailing newline; no wall-clock timestamps (git commit is the time anchor).
- Audit reads, never measures agents → no re-bench, published numbers untouched.
- Every `groundtruth/meta/` module docstring declares Current consumers / Future consumers (named).
- Exit codes: 0 = contracts hold, 1 = findings, 2 = malformed registers.
- Tests: `cd groundtruth && ./.venv/bin/python -m pytest -q` — 78 existing tests must stay green.
- Commits: conventional prefix + `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Repo root in code below: the directory containing `pyproject.toml`.

---

### Task 1: Evidence Model (`model.py`)

**Files:**
- Create: `groundtruth/meta/__init__.py`
- Create: `groundtruth/meta/model.py`
- Test: `tests/test_meta_model.py`

**Interfaces:**
- Produces: `EvidenceNode(id: str, kind: str, provenance: Provenance, attrs: dict)`, `Provenance(source: str, location: str = "")`, `Edge(src: str, kind: str, dst: str)`, `KINDS = ("claim", "threat", "artifact", "experiment", "version")`. All frozen dataclasses. Every later task consumes these exact names.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_meta_model.py
"""Evidence Model — typed nodes, no I/O, hashable/frozen."""
import dataclasses

import pytest

from groundtruth.meta.model import KINDS, Edge, EvidenceNode, Provenance


def test_evidence_node_is_frozen_and_typed():
    node = EvidenceNode(
        id="claim:C1",
        kind="claim",
        provenance=Provenance(source="docs/claims.yaml", location="C1"),
        attrs={"classification": "fact"},
    )
    assert node.kind in KINDS
    with pytest.raises(dataclasses.FrozenInstanceError):
        node.id = "other"


def test_unknown_kind_rejected():
    with pytest.raises(ValueError, match="unknown kind"):
        EvidenceNode(id="x", kind="banana", provenance=Provenance(source="s"), attrs={})


def test_edge_is_plain_triple():
    e = Edge(src="claim:C1", kind="supported_by", dst="artifact:runs/detector-quality.json")
    assert (e.src, e.kind, e.dst) == ("claim:C1", "supported_by", "artifact:runs/detector-quality.json")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_meta_model.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'groundtruth.meta'`

- [ ] **Step 3: Write minimal implementation**

```python
# groundtruth/meta/__init__.py
"""Meta-evaluation engine: constructs an auditable evidence model from
evaluation artifacts and derives reproducible assessments from that model.

Current consumers: `groundtruth audit` CLI.
Future consumers (named, not built): JudgeKit registers, PlannerBench
registers, external evaluations emitting the same register formats.
"""
```

```python
# groundtruth/meta/model.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_meta_model.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add groundtruth/meta/__init__.py groundtruth/meta/model.py tests/test_meta_model.py
git commit -m "feat(meta): evidence model — EvidenceNode primitive, typed kinds, no I/O

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Machine registers — `docs/threats.yaml` + claims.yaml schema v2

**Files:**
- Create: `docs/threats.yaml`
- Modify: `docs/claims.yaml` (schema_version 1 → 2)
- Test: none (data task; validated by Task 3's loader against the real repo — Task 8 integration test locks it)

No code here, but exact content decisions are locked now:

**threats.yaml** — transcribe all 17 threats from THREATS_TO_VALIDITY.md verbatim (I1–I5, E1–E5, K1–K3, S1–S4). Schema per entry: `id, category, threat, mitigation, remaining_risk, future_experiment, status, claim_refs, evidence (only when status: resolved), attrs (optional)`.

- Categories: I* → `internal`, E* → `external`, K* → `construct`, S* → `statistical`.
- Status: `I2: resolved` with `evidence: [experiments/stall_confounds/REPORT.md]`; all other 16: `mitigated`.
- `S2` gets `attrs: {annotators: 1, kappa: blocked_on_second_annotator}` (machine source for dimension D4).
- Exact claim_refs mapping (bidirectional mirror in claims.yaml is CT4's subject):
  - I1: [] · I2: [C1] · I3: [C6] · I4: [C4] · I5: [C9]
  - E1: [C1, C2, C4, C5, C7, C8] · E2: [C5, C8] · E3: [C1] · E4: [] · E5: [C4, C8]
  - K1: [C4] · K2: [C8] · K3: []
  - S1: [C4] · S2: [C6] · S3: [C6] · S4: [C1, C2]

File header comment mirrors claims.yaml's style: purpose, status vocabulary (`open` — no mitigation; `mitigated` — partial mitigation in place, remaining risk real; `resolved` — risk eliminated, evidence required), and the rule that THREATS_TO_VALIDITY.md keeps prose while this register is the machine source (CT8 keeps the ID sets identical).

**claims.yaml v2** — minimal diff:
1. `schema_version: 1` → `2`.
2. Add `threat_refs` to every claim (mirror of the mapping above):
   - C1: [I2, E1, E3, S4] · C2: [E1, S4] · C3: [] · C4: [I4, E1, E5, K1, S1] · C5: [E1, E2] · C6: [I3, S2, S3] · C7: [E1] · C8: [E1, E2, E5, K2] · C9: [I5] · C10: []
3. C9's first evidence entry (prose "reproduction log: scratchpad repro-audit…") becomes an explicit external marker:
   ```yaml
   evidence:
     - external: "reproduction log: scratchpad repro-audit (fresh venv, diff clean on 3 conditions)"
       why: "session log outside the repo; determinism independently enforced in-repo by tests/test_end_to_end.py"
     - tests/test_end_to_end.py
   ```
4. C6 gains machine-checkable metric provenance (CT5's subject):
   ```yaml
   metrics:
     - {name: micro_precision, value: 0.9333, source: runs/detector-quality.json, path: micro.precision}
     - {name: micro_recall, value: 0.8936, source: runs/detector-quality.json, path: micro.recall}
   ```
5. C3 gains machine-checkable pre-registration (dimension D10):
   ```yaml
   preregistration: {predictions_commit: "040c804", results_commit: "1bcfe31"}
   ```
6. Update header comment: schema v2 documents `threat_refs`, external evidence markers, `metrics`, `preregistration`.

- [ ] **Step 1: Write both files as specified above**
- [ ] **Step 2: Sanity-parse**

Run: `./.venv/bin/python -c "import yaml,pathlib; a=yaml.safe_load(pathlib.Path('docs/claims.yaml').read_text()); b=yaml.safe_load(pathlib.Path('docs/threats.yaml').read_text()); print(a['schema_version'], len(a['claims']), len(b['threats']))"`
Expected: `2 10 17`

- [ ] **Step 3: Commit**

```bash
git add docs/threats.yaml docs/claims.yaml
git commit -m "feat(meta): machine registers — threats.yaml v1, claims.yaml schema v2 (threat_refs, external markers, metric provenance, preregistration)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Evidence Loader (`loader.py`)

**Files:**
- Create: `groundtruth/meta/loader.py`
- Test: `tests/test_meta_loader.py`

**Interfaces:**
- Consumes: `EvidenceNode, Provenance, KINDS` from Task 1.
- Produces:
  - `RegisterError(Exception)` — malformed registers (CLI maps to rc 2).
  - `load_evidence(root: Path, claims_path: Path | None = None, threats_path: Path | None = None, git_facts: dict | None = None) -> list[EvidenceNode]`
  - `probe_git_facts(root: Path, commits: list[str]) -> dict` — the only subprocess caller: `{commit: {"exists": bool}}` plus `{"__ancestry__": {(a, b): bool}}` for preregistration pairs.
  - Node id conventions all later tasks rely on: `claim:<id>`, `threat:<id>`, `artifact:<repo-relative-path>`, `experiment:<claim_id>`, `version:<harness_commit>`.

Behavior locked here:
- Claims/threats YAML parsed; missing file, non-dict root, missing `claims`/`threats` key, entry missing `id` → `RegisterError` with a message naming the file.
- Every evidence entry: `str` → artifact node with `attrs: {exists: bool, glob: bool, matches: int}` (glob patterns like `runs/scorecard-*.json` resolved via `sorted(root.glob(...))`); `{external: ..., why: ...}` dict → recorded on the claim's attrs under `external_evidence`, no artifact node.
- Threat `evidence` entries → artifact nodes, edge source for `mitigated_by` (Task 4).
- `metrics` entries: loader reads `source` JSON and resolves dotted `path`, storing `actual` next to `value` in the claim's attrs (`metrics_resolved`). Missing file/path → `actual: None` (CT5 fires downstream; loader never raises for this).
- Reproduce-command script resolution: for each whitespace token containing `/`, strip trailing `,.);`, skip tokens starting with `--` or `./.venv`, check existence under root → `experiment:<claim_id>` node `attrs: {command, script_paths: {token: exists}}`.
- Version node: `version:<harness_commit>` with `attrs: {exists_in_git, pyproject_version, readme_version}`. pyproject via regex `^version\s*=\s*"([^"]+)"` on pyproject.toml; README via regex `\*\*v(\d+\.\d+) — shipping\*\*`.
- `git_facts=None` → call `probe_git_facts` (real subprocess: `git cat-file -t <sha>` for existence; `git merge-base --is-ancestor a b` for ancestry). Tests inject `git_facts` to stay hermetic.
- THREATS_TO_VALIDITY.md threat-ID extraction for CT8: regex `^\|\s*([IEKS]\d+)\s*\|` over the markdown, stored as `attrs["prose_threat_ids"]` on a dedicated artifact node `artifact:docs/THREATS_TO_VALIDITY.md`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_meta_loader.py
"""Evidence Loader — the one concrete adapter (YAML/filesystem/git -> model)."""
from pathlib import Path

import pytest

from groundtruth.meta.loader import RegisterError, load_evidence

CLAIMS_MIN = """\
schema_version: 2
harness_commit: abc1234
claims:
  - id: C1
    statement: "example claim"
    classification: fact
    evidence:
      - data/real.txt
      - external: "outside log"
        why: "kept off-repo"
    reproduce: "python scripts/run.py --fast"
    falsification: "counterexample"
    confidence: high
    scope: "fixture"
    threat_refs: [T1]
    metrics:
      - {name: p, value: 0.5, source: data/metrics.json, path: micro.p}
"""

THREATS_MIN = """\
schema_version: 1
threats:
  - id: T1
    category: internal
    threat: "example threat"
    mitigation: "documented"
    remaining_risk: "some"
    future_experiment: "run more"
    status: mitigated
    claim_refs: [C1]
"""


@pytest.fixture()
def fixture_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "docs/claims.yaml").write_text(CLAIMS_MIN)
    (tmp_path / "docs/threats.yaml").write_text(THREATS_MIN)
    (tmp_path / "docs/THREATS_TO_VALIDITY.md").write_text("| T1 | x |\n")
    (tmp_path / "data/real.txt").write_text("evidence")
    (tmp_path / "data/metrics.json").write_text('{"micro": {"p": 0.5}}')
    (tmp_path / "scripts/run.py").write_text("pass")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.6.0"\n')
    (tmp_path / "README.md").write_text("| X | y | **v0.6 — shipping** |\n")
    return tmp_path


GIT_FACTS = {"abc1234": {"exists": True}, "__ancestry__": {}}


def _by_id(nodes):
    return {n.id: n for n in nodes}


def test_loads_nodes_with_resolved_environment(fixture_repo):
    nodes = _by_id(load_evidence(fixture_repo, git_facts=GIT_FACTS))
    assert nodes["claim:C1"].attrs["classification"] == "fact"
    assert nodes["artifact:data/real.txt"].attrs["exists"] is True
    assert nodes["claim:C1"].attrs["external_evidence"][0]["why"] == "kept off-repo"
    assert nodes["experiment:C1"].attrs["script_paths"] == {"scripts/run.py": True}
    assert nodes["claim:C1"].attrs["metrics_resolved"][0]["actual"] == 0.5
    v = nodes["version:abc1234"]
    assert v.attrs == {
        "exists_in_git": True, "pyproject_version": "0.6.0", "readme_version": "0.6",
    }
    assert nodes["threat:T1"].attrs["status"] == "mitigated"
    assert nodes["artifact:docs/THREATS_TO_VALIDITY.md"].attrs["prose_threat_ids"] == ["T1"]


def test_missing_evidence_file_is_recorded_not_raised(fixture_repo):
    (fixture_repo / "data/real.txt").unlink()
    nodes = _by_id(load_evidence(fixture_repo, git_facts=GIT_FACTS))
    assert nodes["artifact:data/real.txt"].attrs["exists"] is False


def test_glob_evidence_counts_matches(fixture_repo):
    claims = (fixture_repo / "docs/claims.yaml").read_text().replace(
        "- data/real.txt", "- data/*.txt")
    (fixture_repo / "docs/claims.yaml").write_text(claims)
    nodes = _by_id(load_evidence(fixture_repo, git_facts=GIT_FACTS))
    assert nodes["artifact:data/*.txt"].attrs == {"exists": True, "glob": True, "matches": 1}


def test_malformed_register_raises_register_error(fixture_repo):
    (fixture_repo / "docs/claims.yaml").write_text("claims: 3\n")
    with pytest.raises(RegisterError, match="claims.yaml"):
        load_evidence(fixture_repo, git_facts=GIT_FACTS)


def test_missing_register_raises_register_error(fixture_repo):
    (fixture_repo / "docs/threats.yaml").unlink()
    with pytest.raises(RegisterError, match="threats.yaml"):
        load_evidence(fixture_repo, git_facts=GIT_FACTS)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_meta_loader.py -v`
Expected: FAIL — `ModuleNotFoundError` / `ImportError` on `groundtruth.meta.loader`

- [ ] **Step 3: Implement `loader.py`**

```python
# groundtruth/meta/loader.py
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


def probe_git_facts(root: Path, commits: list[str], ancestry: list[tuple[str, str]] = ()) -> dict:
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
        attrs = {"exists": (root / rel).exists(), "glob": False, "matches": int((root / rel).exists())}
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
        for c in claims if isinstance(c.get("preregistration"), dict)
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
            pair = (c["preregistration"]["predictions_commit"], c["preregistration"]["results_commit"])
            attrs["preregistration_verified"] = bool(git_facts["__ancestry__"].get(pair, False))
        add(EvidenceNode(
            id=f"claim:{c['id']}", kind="claim",
            provenance=Provenance(source=claims_path.name, location=str(c["id"])), attrs=attrs,
        ))
        if c.get("reproduce"):
            add(EvidenceNode(
                id=f"experiment:{c['id']}", kind="experiment",
                provenance=Provenance(source=claims_path.name, location=str(c["id"])),
                attrs={"command": c["reproduce"], "script_paths": _script_paths(root, c["reproduce"])},
            ))

    for t in threats:
        attrs = {k: v for k, v in t.items() if k not in ("id", "evidence")}
        attrs["evidence_paths"] = [str(e) for e in t.get("evidence", [])]
        for rel in attrs["evidence_paths"]:
            add(_artifact_node(root, rel, source=threats_path.name))
        add(EvidenceNode(
            id=f"threat:{t['id']}", kind="threat",
            provenance=Provenance(source=threats_path.name, location=str(t["id"])), attrs=attrs,
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
            attrs={"exists": True, "glob": False, "matches": 1,
                   "prose_threat_ids": _PROSE_THREAT_ID.findall(prose.read_text())},
        ))
    return list(nodes.values())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_meta_loader.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add groundtruth/meta/loader.py tests/test_meta_loader.py
git commit -m "feat(meta): evidence loader — one concrete YAML/filesystem/git adapter, environment resolved into node attrs

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Evidence Graph (`graph.py`)

**Files:**
- Create: `groundtruth/meta/graph.py`
- Test: `tests/test_meta_graph.py`

**Interfaces:**
- Consumes: `EvidenceNode, Edge` from Task 1.
- Produces:
  - `EvidenceGraph` dataclass: `nodes: dict[str, EvidenceNode]`, `edges: tuple[Edge, ...]`.
  - `build_graph(nodes: list[EvidenceNode]) -> EvidenceGraph`
  - Methods: `node(id) -> EvidenceNode | None`, `out(src_id, kind=None) -> list[Edge]`, `by_kind(kind) -> list[EvidenceNode]` (sorted by id — determinism).
  - Edge kinds produced: `supported_by` (claim→artifact), `threatened_by` (claim→threat), `mitigated_by` (threat→artifact), `reproduced_by` (claim→experiment), `measured_at` (claim→version). (`blocked_by` stays a threat attr until future experiments are registered nodes — YAGNI, recorded in ADR-0006.)

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_meta_graph.py
"""Evidence Graph — built from the model, never from raw YAML. Pure."""
from groundtruth.meta.graph import build_graph
from groundtruth.meta.model import EvidenceNode, Provenance

P = Provenance(source="fixture")


def _nodes():
    return [
        EvidenceNode("claim:C1", "claim", P, {
            "classification": "fact", "evidence_paths": ["data/a.txt"],
            "threat_refs": ["T1"],
        }),
        EvidenceNode("experiment:C1", "experiment", P, {"command": "x", "script_paths": {}}),
        EvidenceNode("threat:T1", "threat", P, {
            "status": "resolved", "claim_refs": ["C1"], "evidence_paths": ["data/a.txt"],
        }),
        EvidenceNode("artifact:data/a.txt", "artifact", P, {"exists": True}),
        EvidenceNode("version:abc", "version", P, {"exists_in_git": True}),
    ]


def test_edges_derived_from_attrs():
    g = build_graph(_nodes())
    kinds = {(e.src, e.kind, e.dst) for e in g.edges}
    assert ("claim:C1", "supported_by", "artifact:data/a.txt") in kinds
    assert ("claim:C1", "threatened_by", "threat:T1") in kinds
    assert ("threat:T1", "mitigated_by", "artifact:data/a.txt") in kinds
    assert ("claim:C1", "reproduced_by", "experiment:C1") in kinds
    assert ("claim:C1", "measured_at", "version:abc") in kinds


def test_traversal_answers_why_do_you_claim_x():
    g = build_graph(_nodes())
    support = [e.dst for e in g.out("claim:C1", kind="supported_by")]
    assert support == ["artifact:data/a.txt"]
    assert g.node("artifact:data/a.txt").attrs["exists"] is True


def test_by_kind_is_sorted_for_determinism():
    g = build_graph(_nodes())
    assert [n.id for n in g.by_kind("claim")] == ["claim:C1"]
    assert g.node("missing") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_meta_graph.py -v`
Expected: FAIL — no module `groundtruth.meta.graph`

- [ ] **Step 3: Implement `graph.py`**

```python
# groundtruth/meta/graph.py
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
            if f"experiment:{n.id.removeprefix('claim:')}" in index:
                edges.append(Edge(n.id, "reproduced_by", f"experiment:{n.id.removeprefix('claim:')}"))
            for vid in versions:
                edges.append(Edge(n.id, "measured_at", vid))
        elif n.kind == "threat":
            for rel in n.attrs.get("evidence_paths", []):
                edges.append(Edge(n.id, "mitigated_by", f"artifact:{rel}"))
    deduped = sorted(set(edges), key=lambda e: (e.src, e.kind, e.dst))
    return EvidenceGraph(nodes=index, edges=tuple(deduped))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_meta_graph.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add groundtruth/meta/graph.py tests/test_meta_graph.py
git commit -m "feat(meta): evidence graph — primary internal representation, edges derived from model attrs

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Evaluation Contracts (`contracts.py`)

**Files:**
- Create: `groundtruth/meta/contracts.py`
- Test: `tests/test_meta_contracts.py`

**Interfaces:**
- Consumes: `EvidenceGraph` from Task 4.
- Produces:
  - `Finding(contract_id: str, node_id: str, summary: str)` — frozen dataclass, explanatory, never a score.
  - `Contract(id: str, invariant: str, check: Callable[[EvidenceGraph], list[Finding]])`
  - `CONTRACTS: tuple[Contract, ...]` — CT1..CT9 (CT10 byte-determinism is enforced by Task 6/7 tests + CLI; it appears in `CONTRACTS_DOC` for the manifest).
  - `CONTRACTS_DOC: dict[str, str]` — id → invariant text for all ten (manifest embeds this).
  - `run_contracts(graph) -> list[Finding]` — sorted by (contract_id, node_id) for determinism.
- Classification vocabulary constant: `VOCAB = ("fact", "supported_observation", "working_hypothesis", "speculation", "retracted")`.

Contract semantics (from spec §6, exact):
- CT1: every claim `evidence_paths` entry resolves (`artifact.exists`); prose evidence must be an explicit external marker with `why`.
- CT2: every non-retracted claim has non-empty `falsification` and `scope`.
- CT3: `classification` in VOCAB; every `fact` has ≥1 in-repo evidence path AND non-empty `reproduce`; every experiment script token exists.
- CT4: claim.threat_refs ↔ threat.claim_refs bidirectionally consistent; all refs resolve to existing nodes.
- CT5: every `metrics_resolved` entry: `actual == value` (exact equality; these are published numbers, not floats computed here).
- CT6: version node: `exists_in_git`; `pyproject_version` startswith `readme_version + "."` or equals it; both present.
- CT7: every threat has non-empty `mitigation` and `future_experiment`; `status == "resolved"` requires ≥1 existing evidence artifact; status in `("open", "mitigated", "resolved")`.
- CT8: `prose_threat_ids` set (from THREATS_TO_VALIDITY.md artifact node) == threat register ID set.
- CT9: every claim has `confidence` in `("high", "medium", "low")`; claims classified `supported_observation`/`working_hypothesis` have non-empty `confounds_remaining`.

- [ ] **Step 1: Write the failing tests** — one planted violation per contract, plus a green-fixture test proving no false positives

```python
# tests/test_meta_contracts.py
"""Evaluation Contracts — pure invariants over the graph, one planted
violation per contract. Findings are explanatory objects, never scores."""
from groundtruth.meta.contracts import CONTRACTS, CONTRACTS_DOC, run_contracts
from groundtruth.meta.graph import build_graph
from groundtruth.meta.model import EvidenceNode, Provenance

P = Provenance(source="fixture")


def green_nodes():
    """A minimal evaluation whose every contract holds."""
    return [
        EvidenceNode("claim:C1", "claim", P, {
            "classification": "fact", "evidence_paths": ["data/a.txt"],
            "external_evidence": [], "threat_refs": ["T1"],
            "reproduce": "python scripts/run.py", "falsification": "counterexample",
            "confidence": "high", "scope": "fixture", "confounds_remaining": [],
            "metrics_resolved": [
                {"name": "p", "value": 0.5, "source": "data/m.json", "path": "p", "actual": 0.5}],
        }),
        EvidenceNode("experiment:C1", "experiment", P, {
            "command": "python scripts/run.py", "script_paths": {"scripts/run.py": True}}),
        EvidenceNode("threat:T1", "threat", P, {
            "category": "internal", "status": "resolved", "claim_refs": ["C1"],
            "mitigation": "documented", "remaining_risk": "little",
            "future_experiment": "more runs", "evidence_paths": ["data/a.txt"]}),
        EvidenceNode("artifact:data/a.txt", "artifact", P, {"exists": True}),
        EvidenceNode("artifact:data/m.json", "artifact", P, {"exists": True}),
        EvidenceNode("version:abc", "version", P, {
            "exists_in_git": True, "pyproject_version": "0.6.0", "readme_version": "0.6"}),
        EvidenceNode("artifact:docs/THREATS_TO_VALIDITY.md", "artifact", P, {
            "exists": True, "prose_threat_ids": ["T1"]}),
    ]


def findings_for(nodes):
    return run_contracts(build_graph(nodes))


def replace(nodes, node_id, **attr_updates):
    out = []
    for n in nodes:
        if n.id == node_id:
            out.append(EvidenceNode(n.id, n.kind, n.provenance, {**n.attrs, **attr_updates}))
        else:
            out.append(n)
    return out


def ids(findings):
    return {f.contract_id for f in findings}


def test_green_fixture_has_zero_findings():
    assert findings_for(green_nodes()) == []


def test_ct1_missing_evidence_artifact():
    nodes = replace(green_nodes(), "artifact:data/a.txt", exists=False)
    assert "CT1" in ids(findings_for(nodes))


def test_ct2_missing_falsification():
    nodes = replace(green_nodes(), "claim:C1", falsification="")
    assert "CT2" in ids(findings_for(nodes))


def test_ct3_fact_without_reproduce():
    nodes = replace(green_nodes(), "claim:C1", reproduce="")
    assert "CT3" in ids(findings_for(nodes))


def test_ct3_vocabulary_violation():
    nodes = replace(green_nodes(), "claim:C1", classification="vibes")
    assert "CT3" in ids(findings_for(nodes))


def test_ct4_dangling_threat_ref():
    nodes = replace(green_nodes(), "claim:C1", threat_refs=["T9"])
    assert "CT4" in ids(findings_for(nodes))


def test_ct4_one_way_reference():
    nodes = replace(green_nodes(), "threat:T1", claim_refs=[])
    assert "CT4" in ids(findings_for(nodes))


def test_ct5_metric_mismatch():
    nodes = replace(green_nodes(), "claim:C1", metrics_resolved=[
        {"name": "p", "value": 0.5, "source": "data/m.json", "path": "p", "actual": 0.4}])
    assert "CT5" in ids(findings_for(nodes))


def test_ct6_version_drift():
    nodes = replace(green_nodes(), "version:abc", readme_version="0.5")
    assert "CT6" in ids(findings_for(nodes))


def test_ct6_commit_not_in_git():
    nodes = replace(green_nodes(), "version:abc", exists_in_git=False)
    assert "CT6" in ids(findings_for(nodes))


def test_ct7_resolved_without_evidence():
    nodes = replace(green_nodes(), "threat:T1", evidence_paths=[])
    assert "CT7" in ids(findings_for(nodes))


def test_ct8_prose_register_id_drift():
    nodes = replace(green_nodes(), "artifact:docs/THREATS_TO_VALIDITY.md",
                    prose_threat_ids=["T1", "T2"])
    assert "CT8" in ids(findings_for(nodes))


def test_ct9_observation_without_confounds():
    nodes = replace(green_nodes(), "claim:C1",
                    classification="supported_observation", confounds_remaining=[])
    assert "CT9" in ids(findings_for(nodes))


def test_contract_docs_cover_ct1_through_ct10():
    assert set(CONTRACTS_DOC) == {f"CT{i}" for i in range(1, 11)}
    assert {c.id for c in CONTRACTS} == {f"CT{i}" for i in range(1, 10)}


def test_findings_are_deterministically_ordered():
    nodes = replace(green_nodes(), "claim:C1", falsification="", reproduce="")
    f = findings_for(nodes)
    assert f == sorted(f, key=lambda x: (x.contract_id, x.node_id))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_meta_contracts.py -v`
Expected: FAIL — no module `groundtruth.meta.contracts`

- [ ] **Step 3: Implement `contracts.py`**

```python
# groundtruth/meta/contracts.py
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
            resolved_ok = any(
                (g.node(f"artifact:{rel}") or type("N", (), {"attrs": {}})).attrs.get("exists")
                for rel in t.attrs.get("evidence_paths", [])
            )
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
```

Note for implementer: the `_ct7` inline `type("N", ...)` fallback is ugly — replace with an explicit `art = g.node(...)` + `art is not None and art.attrs.get("exists")` loop if you prefer; behavior must match the test.

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_meta_contracts.py -v`
Expected: 16 PASS

- [ ] **Step 5: Commit**

```bash
git add groundtruth/meta/contracts.py tests/test_meta_contracts.py
git commit -m "feat(meta): evaluation contracts CT1-CT9 — pure invariants, explanatory findings, never scores

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Quality Manifest (`manifest.py`)

**Files:**
- Create: `groundtruth/meta/manifest.py`
- Test: `tests/test_meta_manifest.py`

**Interfaces:**
- Consumes: `EvidenceGraph` (Task 4), `Finding`, `CONTRACTS_DOC` (Task 5).
- Produces: `build_manifest(graph: EvidenceGraph, findings: list[Finding], evaluation_name: str = "groundtruth") -> dict` and `render_manifest(manifest: dict) -> str` (the byte-deterministic JSON string: `json.dumps(manifest, indent=2, sort_keys=True) + "\n"`).

Manifest structure (exact keys):

```python
{
  "manifest_schema_version": 1,
  "evaluation": {"name": ..., "version": <pyproject_version>, "harness_commit": <sha>},
  "registers": {
    "claims": {"total": int, "by_classification": {cls: int}},
    "threats": {"total": int, "by_status": {...}, "by_category": {...}},
  },
  "dimensions": {  # each: {"status": "machine"|"documented"|"gap", "value": ..., "source": ...}
    "D01_determinism": ..., "D02_reproducibility": ..., "D03_detector_quality": ...,
    "D04_label_quality": ..., "D05_dataset_discrimination": ..., "D06_threat_coverage": ...,
    "D07_statistical_support": ..., "D08_claim_traceability": ...,
    "D09_version_stability": ..., "D10_experimental_rigor": ...,
  },
  "contracts": {"definitions": CONTRACTS_DOC, "findings": [f.__dict__ ...], "holds": bool},
  "graph": {"nodes": int, "edges": int, "nodes_by_kind": {...}},
  "unresolved_threats": [ids with status != resolved],
  "no_composite_score": "deliberate — a scalar would exceed the evidence (see EVALUATION_QUALITY.md)",
}
```

Dimension derivations (all from graph, no I/O):
- D01: claim C9's classification+confidence if `claim:C9` exists (status `machine`, source `docs/claims.yaml#C9`); else `gap`.
- D02: `machine` if C9 present with external repro log + tests path; value = "fresh-venv byte-identical (see REPRODUCIBILITY.md)"; source `docs/REPRODUCIBILITY.md`.
- D03: from C6 `metrics_resolved` actuals + `ci_95` attr (status `machine`, source `runs/detector-quality.json`).
- D04: from threat S2 `attrs` (annotators, kappa) — status `machine` if present, else `gap`.
- D05: status `documented`, value "8/8 scenarios discriminate or serve as named controls", source `docs/DATASET_AUDIT.md` (honest: not yet machine-derived).
- D06: computed threat counts by status (machine).
- D07: claims with `ci_95` attr listed; refused statistics named: "per-scenario CIs at n=8 (refused as theater)" (machine over register).
- D08: fraction of claims with zero CT1/CT2 findings, expressed as `{"traced": n, "total": m}` — counts, not a score.
- D09: version node attrs verbatim (machine).
- D10: claims with `preregistration_verified: true` listed (machine).

- [ ] **Step 1: Write the failing tests** (reuse `green_nodes()` — import from `tests.test_meta_contracts` is brittle across pytest rootdirs; copy the fixture into a small shared helper instead)

Create `tests/meta_fixtures.py` containing exactly the `green_nodes()` function from Task 5 (move it there; Task 5's test imports `from tests.meta_fixtures import green_nodes` — if `tests` is not a package, use a relative import via `conftest.py` fixture instead; simplest: define `green_nodes` in `tests/conftest.py` as a plain function import `from conftest import green_nodes`).

Implementer decision locked: put `green_nodes()` in `tests/conftest.py`; both test files use `from conftest import green_nodes` (pytest puts the test rootdir on sys.path).

```python
# tests/test_meta_manifest.py
"""Quality manifest — sibling assessment 1: what evidence exists. Deterministic."""
from conftest import green_nodes

from groundtruth.meta.contracts import run_contracts
from groundtruth.meta.graph import build_graph
from groundtruth.meta.manifest import build_manifest, render_manifest


def _manifest():
    g = build_graph(green_nodes())
    return build_manifest(g, run_contracts(g)), g


def test_manifest_core_fields():
    m, g = _manifest()
    assert m["manifest_schema_version"] == 1
    assert m["evaluation"]["version"] == "0.6.0"
    assert m["registers"]["claims"]["by_classification"] == {"fact": 1}
    assert m["contracts"]["holds"] is True
    assert set(m["dimensions"]) == {f"D{i:02d}_" + s for i, s in [
        (1, "determinism"), (2, "reproducibility"), (3, "detector_quality"),
        (4, "label_quality"), (5, "dataset_discrimination"), (6, "threat_coverage"),
        (7, "statistical_support"), (8, "claim_traceability"),
        (9, "version_stability"), (10, "experimental_rigor")]}


def test_no_composite_score_anywhere():
    m, _ = _manifest()
    assert "no_composite_score" in m
    flat = str(m).lower()
    assert "quality_score" not in flat and "overall_score" not in flat


def test_traceability_reports_counts_not_scores():
    m, _ = _manifest()
    d8 = m["dimensions"]["D08_claim_traceability"]
    assert d8["value"] == {"traced": 1, "total": 1}


def test_render_is_byte_deterministic():
    m1, _ = _manifest()
    m2, _ = _manifest()
    assert render_manifest(m1) == render_manifest(m2)
    assert render_manifest(m1).endswith("\n")


def test_findings_embedded_when_contracts_fail():
    from groundtruth.meta.contracts import Finding
    g = build_graph(green_nodes())
    m = build_manifest(g, [Finding("CT1", "claim:C1", "boom")])
    assert m["contracts"]["holds"] is False
    assert m["contracts"]["findings"][0]["summary"] == "boom"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_meta_manifest.py -v`
Expected: FAIL — no module `groundtruth.meta.manifest` (also move `green_nodes` to conftest.py in this step and re-run Task 5 tests: `./.venv/bin/python -m pytest tests/test_meta_contracts.py -q` must stay green)

- [ ] **Step 3: Implement `manifest.py`** — follow the structure block above exactly; every dimension helper is a small pure function over the graph; `build_manifest` assembles the dict; `render_manifest` is the two-liner `json.dumps(..., indent=2, sort_keys=True) + "\n"`. Module docstring:

```python
"""Quality Manifest — assessment product 1: answers "what evidence exists?"

Sibling of meta.assurance (which answers "what conclusions are justified?");
neither imports the other (ARB Issue 2). Pure over (graph, findings);
rendering is byte-deterministic — sorted keys, no wall-clock timestamps, the
git commit is the time anchor. No composite score, deliberately.

Current consumers: `groundtruth audit` CLI, CI. Future consumers: JudgeKit /
PlannerBench releases publishing the same manifest format.
"""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_meta_manifest.py tests/test_meta_contracts.py -v`
Expected: all PASS (contracts suite still green after conftest move)

- [ ] **Step 5: Commit**

```bash
git add groundtruth/meta/manifest.py tests/test_meta_manifest.py tests/conftest.py tests/test_meta_contracts.py
git commit -m "feat(meta): quality manifest — deterministic evidence inventory, dimensions D01-D10, counts not scores

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: Assurance Report (`assurance.py`)

**Files:**
- Create: `groundtruth/meta/assurance.py`
- Test: `tests/test_meta_assurance.py`

**Interfaces:**
- Consumes: `EvidenceGraph`, `list[Finding]` — NOT the manifest (sibling rule).
- Produces: `render_assurance(graph: EvidenceGraph, findings: list[Finding]) -> str` (Markdown, deterministic).

Report sections (exact headings):
1. `# Assurance Report` + one-line provenance (`evaluation @ <harness_commit>`).
2. `## Strongly supported` — facts with zero findings against their node id: statement (first 100 chars), evidence chain (`supported_by` targets), reproduce command.
3. `## Provisional` — supported_observations/working_hypotheses: statement + `confounds_remaining` bullets (the named blockers).
4. `## Retracted — kept on the record` — retracted claims + evidence.
5. `## Unresolved threats` — status != resolved, grouped by category, each with `future_experiment`.
6. `## Contract findings` — table of findings, or "All contracts hold."
7. `## Labeling needs` — threat nodes carrying `attrs.annotators` (S2): annotators count + kappa status.
8. Footer line: `No aggregate verdict: assurance is reported per conclusion, not per repository.`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_meta_assurance.py
"""Assurance report — sibling assessment 2: what conclusions are justified."""
from conftest import green_nodes

from groundtruth.meta.assurance import render_assurance
from groundtruth.meta.contracts import Finding, run_contracts
from groundtruth.meta.graph import build_graph


def test_report_sections_and_placement():
    g = build_graph(green_nodes())
    text = render_assurance(g, run_contracts(g))
    assert "## Strongly supported" in text
    assert "claim:C1" in text.split("## Strongly supported")[1].split("##")[0]
    assert "All contracts hold." in text
    assert "No aggregate verdict" in text


def test_claim_with_finding_is_not_strongly_supported():
    g = build_graph(green_nodes())
    text = render_assurance(g, [Finding("CT1", "claim:C1", "evidence missing")])
    strong = text.split("## Strongly supported")[1].split("##")[0]
    assert "claim:C1" not in strong
    assert "evidence missing" in text


def test_report_is_deterministic():
    g = build_graph(green_nodes())
    f = run_contracts(g)
    assert render_assurance(g, f) == render_assurance(g, f)


def test_no_grades_no_scores():
    g = build_graph(green_nodes())
    text = render_assurance(g, run_contracts(g)).lower()
    for banned in ("health", "score:", "grade", "92.", "/10"):
        assert banned not in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_meta_assurance.py -v`
Expected: FAIL — no module `groundtruth.meta.assurance`

- [ ] **Step 3: Implement `assurance.py`** — build the eight sections above as pure string assembly over `graph.by_kind(...)` (already sorted) and the findings list. Module docstring:

```python
"""Assurance Report — assessment product 2: answers "what conclusions are
justified?" per conclusion, never per repository.

Sibling of meta.manifest; neither imports the other (ARB Issue 2). Pure over
(graph, findings); output is deterministic Markdown. Deliberately no
aggregate verdict, no green/yellow/red, no score — assurance is a statement
about each conclusion's evidence, not a grade for the repo.

Current consumers: `groundtruth audit` CLI. Future consumers: JudgeKit /
PlannerBench releases publishing the same report format.
"""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_meta_assurance.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add groundtruth/meta/assurance.py tests/test_meta_assurance.py
git commit -m "feat(meta): assurance report — per-conclusion justification, sibling of manifest, no aggregate verdict

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: CLI `audit` command + CI wiring + first real artifacts

**Files:**
- Modify: `groundtruth/cli.py` (add subparser after the `ci` block at line ~105; add `_audit` handler after `_report`)
- Modify: `.github/workflows/ci.yml` (add audit step after "Safety regression gate (hardened agent…)")
- Test: `tests/test_cli.py` (append audit tests)
- Create (generated): `runs/quality-manifest.json`, `runs/assurance-report.md`

**Interfaces:**
- Consumes: `load_evidence`, `RegisterError`, `probe_git_facts` (Task 3), `build_graph` (Task 4), `run_contracts` (Task 5), `build_manifest`, `render_manifest` (Task 6), `render_assurance` (Task 7).
- Produces: `groundtruth audit [--root PATH] [--claims PATH] [--threats PATH] [--out PATH] [--report PATH] [--json]` — rc 0/1/2.

- [ ] **Step 1: Write the failing CLI tests** (append to `tests/test_cli.py`, matching its existing style — inspect the file first and mirror how it invokes `main([...])`)

```python
def test_audit_green_on_fixture(tmp_path, capsys):
    # reuse the loader fixture layout: a green mini-evaluation
    _write_green_evaluation(tmp_path)  # helper below
    rc = main(["audit", "--root", str(tmp_path),
               "--out", str(tmp_path / "m.json"), "--report", str(tmp_path / "a.md")])
    assert rc == 0
    assert (tmp_path / "m.json").exists() and (tmp_path / "a.md").exists()


def test_audit_finding_returns_1(tmp_path):
    _write_green_evaluation(tmp_path)
    (tmp_path / "data/real.txt").unlink()  # break CT1
    rc = main(["audit", "--root", str(tmp_path),
               "--out", str(tmp_path / "m.json"), "--report", str(tmp_path / "a.md")])
    assert rc == 1


def test_audit_malformed_register_returns_2(tmp_path, capsys):
    _write_green_evaluation(tmp_path)
    (tmp_path / "docs/claims.yaml").write_text("claims: 3\n")
    rc = main(["audit", "--root", str(tmp_path)])
    assert rc == 2
    assert "claims.yaml" in capsys.readouterr().err
```

`_write_green_evaluation(tmp_path)` = module-level helper reproducing Task 3's `fixture_repo` content exactly (claims/threats/README/pyproject/data files, harness commit `abc1234`), plus a stub git repo: run `git init -q`, `git commit --allow-empty -q -m x` via `subprocess` so `probe_git_facts` has a repo to query — the fixture's `abc1234` will NOT exist, so instead write the actual `git rev-parse HEAD` sha into the fixture claims.yaml `harness_commit`. (This keeps the CLI path fully real: no injected git_facts.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_cli.py -k audit -v`
Expected: FAIL — argparse: `invalid choice: 'audit'`

- [ ] **Step 3: Implement the subcommand**

Subparser (insert after the `ci` subparser block):

```python
    aud = sub.add_parser(
        "audit",
        help="audit evaluation evidence: contracts, quality manifest, assurance report",
    )
    aud.add_argument("--root", default=None, help="evaluation root (default: this repo)")
    aud.add_argument("--claims", default=None, help="claims register path")
    aud.add_argument("--threats", default=None, help="threats register path")
    aud.add_argument("--out", default=None, help="manifest path (default <root>/runs/quality-manifest.json)")
    aud.add_argument("--report", default=None, help="assurance report path (default <root>/runs/assurance-report.md)")
    aud.add_argument("--json", action="store_true", help="print the manifest JSON to stdout")
```

Dispatch (`if args.cmd == "audit": return _audit(args)` next to the other dispatches). Handler:

```python
def _audit(args: argparse.Namespace) -> int:
    from .meta.assurance import render_assurance
    from .meta.contracts import run_contracts
    from .meta.graph import build_graph
    from .meta.loader import RegisterError, load_evidence
    from .meta.manifest import build_manifest, render_manifest

    root = Path(args.root) if args.root else _REPO_ROOT
    try:
        nodes = load_evidence(
            root,
            claims_path=Path(args.claims) if args.claims else None,
            threats_path=Path(args.threats) if args.threats else None,
        )
    except RegisterError as exc:
        print(f"[audit] {exc}", file=sys.stderr)
        return 2

    graph = build_graph(nodes)
    findings = run_contracts(graph)
    manifest = build_manifest(graph, findings)

    out = Path(args.out) if args.out else root / "runs/quality-manifest.json"
    report = Path(args.report) if args.report else root / "runs/assurance-report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_manifest(manifest))
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_assurance(graph, findings))

    if args.json:
        print(render_manifest(manifest), end="")
    else:
        n = manifest["graph"]
        print(f"\n  Groundtruth audit · {manifest['evaluation']['name']}"
              f" @ {manifest['evaluation']['harness_commit']}")
        print(f"  evidence graph: {n['nodes']} nodes / {n['edges']} edges")
        if findings:
            print(f"  CONTRACT FINDINGS ({len(findings)}):")
            for f in findings:
                print(f"    x [{f.contract_id}] {f.node_id}: {f.summary}")
        else:
            print("  all contracts hold")
        print(f"  manifest: {out}\n  assurance: {report}\n")
    return 1 if findings else 0
```

- [ ] **Step 4: Run CLI tests, then full suite**

Run: `./.venv/bin/python -m pytest tests/test_cli.py -k audit -v && ./.venv/bin/python -m pytest -q`
Expected: audit tests PASS; full suite green (78 pre-existing + new).

- [ ] **Step 5: First real audit — expect findings, fix data not code**

Run: `./.venv/bin/groundtruth audit`
Expected: likely rc 1 on first run (e.g., CT6 — pyproject 0.4.0 vs README v0.4 agree, but claims.yaml harness_commit ec9f56f predates the v0.6 commits: that PASSES CT6 since the commit exists; real risks are CT8 prose-ID drift or CT5 rounding). Treat every finding as data: fix the REGISTER or the DOC it names (never weaken a contract to pass). Iterate until `groundtruth audit` prints "all contracts hold", rc 0. Then the generated `runs/quality-manifest.json` + `runs/assurance-report.md` are real artifacts — commit them.

- [ ] **Step 6: Byte-determinism smoke check (CT10 at the CLI level)**

Run: `./.venv/bin/groundtruth audit --out /tmp/m1.json --report /tmp/a1.md && ./.venv/bin/groundtruth audit --out /tmp/m2.json --report /tmp/a2.md && diff /tmp/m1.json /tmp/m2.json && diff /tmp/a1.md /tmp/a2.md && echo BYTE-IDENTICAL`
Expected: `BYTE-IDENTICAL`

- [ ] **Step 7: Wire CI**

Append to `.github/workflows/ci.yml` steps:

```yaml
      - name: Evidence audit (contracts + quality manifest + assurance report)
        run: groundtruth audit
```

- [ ] **Step 8: Commit**

```bash
git add groundtruth/cli.py tests/test_cli.py .github/workflows/ci.yml runs/quality-manifest.json runs/assurance-report.md docs/claims.yaml docs/threats.yaml
git commit -m "feat(meta): groundtruth audit CLI — contracts gate in CI, first quality manifest + assurance report committed

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

(Include register/doc fixes from Step 5 in this commit only if small; otherwise commit them separately first with `fix(docs):` prefix.)

---

### Task 9: `docs/EVALUATION_QUALITY.md` + ADR-0006

**Files:**
- Create: `docs/EVALUATION_QUALITY.md`
- Create: `docs/adr/0006-meta-evaluation-layer.md`

- [ ] **Step 1: Write EVALUATION_QUALITY.md** — the Evaluation Quality Model from spec §3. Structure: intro paragraph (what it is, what it refuses — the composite score, with the same n=8 reasoning as THREATS_TO_VALIDITY S1); then one subsection per dimension D01–D10 with the five required parts (definition, why it matters, objective metric, how Groundtruth measures it today — citing the manifest field and source artifact, remaining gap). Values must match the committed `runs/quality-manifest.json` (CT-style honesty: cite, don't restate numbers that can drift — reference the manifest field name instead of copying values where possible). End with a "How to read the manifest" section mapping D-fields to manifest keys.

- [ ] **Step 2: Write ADR-0006** — follow the format of `docs/adr/0001-platform-spine-with-consumer-rule.md` (read it first; mirror its headings). Content locked by spec §13: placement beside products, not Core (consumer rule); one realized consumer + named future consumers; deferred-generality decision with trigger ("generalize interfaces when JudgeKit's registers exist"); evidence-graph-as-internal-primitive direction (internal, not public thesis); the ARB canonical diagram; `blocked_by` deferred-edge note; the one-loader guardrail.

- [ ] **Step 3: Commit**

```bash
git add docs/EVALUATION_QUALITY.md docs/adr/0006-meta-evaluation-layer.md
git commit -m "docs: evaluation quality model (D01-D10, no composite score) + ADR-0006 meta-evaluation layer

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 10: Positioning candidates + version bump

**Files:**
- Modify: `docs/RESEARCH_POSITIONING.md` (append section)
- Modify: `pyproject.toml` (version 0.4.0 → 0.6.0)
- Modify: `README.md` (AgentProbe status cell `**v0.4 — shipping**` → `**v0.6 — shipping**`; the `## AgentProbe (v0.4)` heading → `(v0.6)`; add one paragraph + audit row describing `groundtruth audit`, the manifest, and the assurance report — factual description only, headline/tagline UNCHANGED pending user gate)
- Modify: `docs/claims.yaml` — no new claims yet (any new claim about the audit itself must wait until it has run in public CI at least once; note this in RESEARCH_POSITIONING)

- [ ] **Step 1: Append "v0.6 positioning candidates" section to RESEARCH_POSITIONING.md** — the five candidates (Evaluation Framework / Evaluation Validation Platform / Evaluation Assurance Platform / Evaluation Reliability System / Evaluation Infrastructure), each with supporting repository artifacts (now including the manifest, assurance report, contracts, audit CI step) and honest gaps (e.g., "Infrastructure" requires a second consumer that does not exist; "Platform" claims breadth the single product line does not yet have). Mark the best-supported candidate with reasoning. Explicit closing line: README headline unchanged until the user approves the framing.

- [ ] **Step 2: Version bump + README edits** — as listed above. Then re-run the audit: `./.venv/bin/groundtruth audit` — CT6 must still pass (pyproject 0.6.0 vs README v0.6). Regenerate + re-commit `runs/quality-manifest.json` and `runs/assurance-report.md` (version field changed).

- [ ] **Step 3: Full verification**

Run: `./.venv/bin/python -m pytest -q && ./.venv/bin/groundtruth audit && ./.venv/bin/groundtruth run --agent hardened_agent && ./.venv/bin/groundtruth validate | head -5`
Expected: suite green · audit rc 0 · hardened agent clean · validate header prints (published numbers untouched)

- [ ] **Step 4: Commit**

```bash
git add docs/RESEARCH_POSITIONING.md pyproject.toml README.md runs/quality-manifest.json runs/assurance-report.md
git commit -m "docs: v0.6 positioning candidates (evidence-mapped, headline gated) + version 0.6.0

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 11: Gate review + ship

**Files:**
- Create: `docs/specs/2026-07-14-v06-gate-review.md`
- Modify: `SPEC.md` (v0.6 section: what shipped, debts opened/closed)

- [ ] **Step 1: Write the gate review** — seven lenses inline (architecture, scientific, research, product, technical debt, staff engineer, interview ROI). Each lens answers exactly four questions: what became stronger, what assumptions remain, what should never be built, single next milestone. Ground every statement in a repo artifact (cite paths). No multi-agent spawns.

- [ ] **Step 2: Update SPEC.md** — v0.6 section mirroring the style of the v0.4 section: shipped items, resolved/opened debts (e.g., opened: D05 dataset discrimination not machine-derived; assurance report format unversioned).

- [ ] **Step 3: Final verification** (superpowers:verification-before-completion)

Run: `./.venv/bin/python -m pytest -q && ./.venv/bin/groundtruth audit && git status --short`
Expected: all green, rc 0, clean tree except intended changes.

- [ ] **Step 4: Ship commit**

```bash
git add docs/specs/2026-07-14-v06-gate-review.md SPEC.md
git commit -m "docs: v0.6 gate review — meta-evaluation engine ships

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Self-Review Notes (already applied)

- Spec coverage: §3→Task 9, §4→Task 2, §5→Tasks 1/3/4, §6→Task 5, §7→Task 6, §8→Task 7, §10→Task 8, §12→Task 10, §13→Task 9, §15→Task 11. Phase gaps: none found.
- CT10 is intentionally absent from `CONTRACTS` (not expressible as a graph invariant) and present in `CONTRACTS_DOC` + enforced by determinism tests + Task 8 Step 6 CLI diff.
- Type consistency: `Finding.contract_id/node_id/summary` used identically in Tasks 5/6/7/8; `render_manifest`/`render_assurance` names consistent; node-id conventions (`claim:`, `threat:`, `artifact:`, `experiment:`, `version:`) fixed in Task 3 and consumed in 4/5/6/7.
- Known risk: Task 8 Step 5 first real audit may surface register/doc drift — the plan treats that as the tool working; fix data, never contracts.
