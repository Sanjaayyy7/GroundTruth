# v0.6 Design — Meta-Evaluation Engine

- **Status:** Frozen for implementation (ARB conditionally approved 2026-07-14; five modifications incorporated below)
- **Directive:** v0.6 "Meta-Evaluation Engine" — measure the quality of evaluations, not only model behavior
- **Baseline:** main @ 65c146e, 78/78 tests green, v0.5 evidence artifacts complete

## 1. Objective

One new subsystem: `groundtruth audit`. It **constructs an auditable evidence model from
evaluation artifacts and derives reproducible assessments from that model.** The engine's
primary internal representation is the Evidence Graph — files (claims.yaml,
threats.yaml, runs/, git) are persistence adapters, not the architecture. It verifies
evaluation contracts over the graph and emits two sibling assessment products — a quality
manifest (JSON) and an assurance report (Markdown) — deterministically. It fails red on
inconsistency and runs in CI.

Canonical internal model (ARB-mandated, treat as the standing architecture diagram):

```
Evaluation Artifacts
        ↓
Evidence Loader (YAML/filesystem/git — the one concrete adapter)
        ↓
Evidence Model (EvidenceNode and typed nodes; no I/O)
        ↓
Evidence Graph (primary internal representation)
        ↓
Evaluation Contracts (pure invariants over the graph)
      ↙          ↘
Quality Manifest   Assurance Report   (siblings; neither imports the other)
```

The audit **reads, never measures agents**. It is not part of the measurement harness, so
immutable #8 (harness change → full re-bench) is not triggered. No published number changes.

## 2. ARB modifications and dispositions

| # | Modification | Disposition |
|---|---|---|
| 1 | Engine must evaluate *any* evaluation | **Core accepted, full generality rejected** (ADR-0001). Engine is parameterized: evaluation root + register paths as inputs, no Groundtruth literals inside `meta/`. Register schemas are versioned, documented *formats* — the reusable surface. Generic Python abstraction layer deferred with a named trigger: build it when JudgeKit's registers exist and reveal what a second consumer needs. |
| 2 | Explicit Evidence Graph | **Accepted.** `graph.py`, plain dataclasses, no graph library, no visualization. Three internal consumers from day one: contracts, manifest, assurance. |
| 3 | Evaluation Contracts, not checks | **Accepted.** Declarative invariants with IDs; each contract carries its machine enforcement. No contract DSL. |
| 4 | Rename health → assurance | **Accepted.** Output is per-conclusion assurance, never a green/yellow/red status. |
| 5 | Document current/future consumers per module | **Accepted.** Module docstring header lists named current and future consumers. |
| — | Do not freeze "evaluation reliability system" | **Accepted.** Positioning produced as evidence-mapped candidates with a marked recommendation; README headline unchanged until user gate. |

## 3. Evaluation Quality Model (Phase 1)

`docs/EVALUATION_QUALITY.md` defines ten dimensions of evaluation trustworthiness. Each
dimension gets: definition, why it matters, objective metric, how Groundtruth currently
measures it, remaining gap.

| # | Dimension | Objective metric (source) |
|---|---|---|
| D1 | Determinism | byte-identity reproduction status per subject (C9, repro log) |
| D2 | Reproducibility | verified reproduction tier and commit (REPRODUCIBILITY.md, fresh-venv audit) |
| D3 | Detector quality | micro P/R + bootstrap 95% CI (runs/detector-quality.json, experiments/detector_quality_ci.py) |
| D4 | Label quality | annotator count, inter-rater κ status (currently 1, κ blocked — disclosed) |
| D5 | Dataset discriminative power | scenarios discriminating / total, per the discrimination matrix (DATASET_AUDIT.md) |
| D6 | Threat coverage | threat counts by status and category (threats.yaml) |
| D7 | Statistical support | which claims carry intervals; which statistics were refused and why |
| D8 | Claim traceability | % of claims whose evidence, falsification, and scope all resolve (audit) |
| D9 | Version stability | harness_commit validity; pyproject == README == manifest version |
| D10 | Experimental rigor | pre-registration verifiable in git (predictions commit precedes results commit) |

**No composite quality score.** A single number would exceed the evidence — same refusal,
same reasoning as per-scenario CIs at n=8. The manifest reports dimensions separately.

## 4. Machine registers (Phase 2 inputs)

- **`docs/threats.yaml`** (new, `schema_version: 1`): one entry per threat —
  `id, category (internal|external|construct|statistical|conclusion), threat, mitigation,
  remaining_risk, future_experiment, status (open|mitigated|resolved), claim_refs`.
  Content transcribed from THREATS_TO_VALIDITY.md tables (I1–I5, E1–E5, K1–K3, S1–S4).
  The markdown keeps its prose; the audit cross-checks that the two ID sets match exactly.
- **`docs/claims.yaml` → `schema_version: 2`**: adds `threat_refs` per claim. No other
  semantic change; existing fields already carry evidence, reproduce, falsification,
  confidence, scope.

These two registers are the engine's *format contract*: any future evaluation that emits
them can be audited by the same engine.

## 5. Evidence Model and Evidence Graph

**Evidence Model (`groundtruth/meta/model.py`)** — the ontology, admitted explicitly.
One base primitive:

- `EvidenceNode` — id, kind, provenance (source artifact + location), attributes.
- Typed nodes: Claim, Threat, EvidenceArtifact, Experiment, Version. Plain dataclasses,
  a `kind` discriminator, no inheritance ceremony, no polymorphism framework.
- The model does **no I/O**. The loader resolves everything environmental — file
  existence, git commit validity, version strings — into node attributes at load time.
  Consequence: every downstream layer (graph, contracts, assessments) is a pure function
  of the model, trivially testable with synthetic fixtures.

**Evidence Graph (`groundtruth/meta/graph.py`)** — primary internal representation.

- **Edges:** `supported_by` (claim → evidence), `threatened_by` (claim → threat),
  `mitigated_by` (threat → mitigation/evidence), `reproduced_by` (claim → command),
  `measured_at` (claim → version), `blocked_by` (threat → future experiment).
- Built from the Evidence Model, never from raw YAML dicts.
- Provenance question the graph answers: "Why do you claim X?" → follow edges from
  claim to artifacts to version.

**Evidence Loader (`groundtruth/meta/loader.py`)** — the one concrete adapter:
YAML registers + filesystem resolution + git facts → Evidence Model.
**Anti-over-engineering guardrail (ARB warning, binding):** exactly one loader. No
abstract base classes, no plugin system, no loader registry, no extension API. The
conceptual layering is enforced by import direction alone:
`loader → model ← graph ← contracts ← {manifest, assurance}`. Room for future consumers
lives in the model's independence from YAML, not in speculative interfaces (ADR-0001).

## 6. Evaluation Contracts (`groundtruth/meta/contracts.py`)

Declarative invariants over the Evidence Graph. Each contract: ID, invariant statement,
machine enforcement, findings emitted as explanatory objects (never scores) — deliberate
symmetry with the detector philosophy (ADR-0002). Contracts are **pure functions of the
graph**: all environmental facts (file existence, git validity) were already resolved
into node attributes by the loader.

| ID | Invariant |
|---|---|
| CT1 | Every claim's evidence references resolve to in-repo artifacts (or are explicitly marked external with justification). |
| CT2 | Every non-retracted claim declares a falsification condition and a scope sentence. |
| CT3 | Classification is in vocabulary; every `fact` has in-repo evidence and a reproduce command whose referenced script/path exists. |
| CT4 | Claim↔threat references are bidirectionally consistent and all resolve. |
| CT5 | Every numeric metric quoted in a claim matches the value in its source artifact (e.g., C6 P/R vs runs/detector-quality.json). |
| CT6 | Version stability: harness_commit exists in git history; pyproject version, README version, and manifest version agree. |
| CT7 | Every threat has a mitigation and a future experiment; `resolved` status requires an evidence reference. |
| CT8 | Threat IDs in THREATS_TO_VALIDITY.md and threats.yaml are identical sets. |
| CT9 | Every claim carries confidence and scope; every non-fact names the experiment that would strengthen it. |
| CT10 | Audit outputs are byte-identical across two runs at the same commit. |

Exit semantics: rc 0 all contracts hold; rc 1 one or more findings; rc 2 malformed
registers (loud parse error, `[audit]` prefix).

## 7. Quality Manifest (`groundtruth/meta/manifest.py` → `runs/quality-manifest.json`)

Assessment product 1: answers **"what evidence exists?"** Inputs: Evidence Graph +
contract findings. Does not import assurance. Derived, versioned, machine-readable.
Deterministic: sorted keys, no wall-clock timestamps — the git commit is the time
anchor. Fields:

- `manifest_schema_version`, `evaluation {name, version, harness_commit}`
- `registers`: claim counts by classification; threat counts by status and category
- `dimensions`: one entry per D1–D10 with its metric value and source artifact path
- `contracts`: pass/fail per CT, findings list
- `graph`: node/edge counts (traceability surface summary)
- `known_limitations`, `unresolved_threats`: derived from threats.yaml status
- `evidence_references`: resolved artifact index

Committed to the repo as a first-class artifact of every release.

## 8. Assurance Report (`groundtruth/meta/assurance.py` → `runs/assurance-report.md`)

Assessment product 2: answers **"what conclusions are justified?"** Inputs: Evidence
Graph + contract findings — the manifest's **sibling**, not its child; neither imports
the other (ARB Issue 2). Deterministic Markdown. Answers, per conclusion:

- **Strongly supported:** facts whose contracts all hold, with their evidence chains.
- **Provisional:** supported observations / hypotheses, each with the named experiment
  that blocks strengthening.
- **Retracted / on record:** kept visible (C3 discipline).
- **Unresolved threats:** by category, with named future experiments.
- **Labeling needs:** annotation coverage gaps (κ status).

No aggregate verdict. Assurance is reported per conclusion, not per repository.

## 9. Package layout and module contracts

```
groundtruth/meta/
├── __init__.py
├── model.py       # Evidence Model — EvidenceNode + typed nodes (no I/O)
├── loader.py      # the one concrete adapter: YAML/filesystem/git → model
├── graph.py       # Evidence Graph — primary internal representation
├── contracts.py   # pure declarative invariants over the graph
├── manifest.py    # assessment product 1: what evidence exists (JSON)
└── assurance.py   # assessment product 2: what conclusions are justified (Markdown)
```

Import direction (enforced, reviewed at gate):
`loader → model ← graph ← contracts ← {manifest, assurance}`; manifest and assurance
never import each other; only `loader.py` performs I/O.

Every module docstring declares:
- **Current consumers:** `groundtruth audit` CLI.
- **Future consumers (named, not built):** JudgeKit registers, PlannerBench registers,
  external evaluation repositories emitting the same register formats.

`meta/` sits beside `products/`, not inside `core/`: the consumer rule (ADR-0001) blocks
Core entry until a second realized consumer exists. If `meta/` reuses Core readers
(e.g., scorecard schema), that is recorded honestly in ADR-0006 — verified during
implementation, not overclaimed.

## 10. CLI and CI

- `groundtruth audit [--root PATH] [--claims PATH] [--threats PATH] [--out runs/quality-manifest.json] [--report runs/assurance-report.md]`
  — defaults resolve to the repository the command runs in; all paths parameterized (Mod 1).
- Added to `.github/workflows/ci.yml` after the test step; findings fail the build.

## 11. Testing strategy (TDD throughout)

- `tests/test_meta_loader.py` — schema validation, environmental resolution into node
  attributes, malformed-register rc 2 behavior.
- `tests/test_meta_graph.py` — node/edge construction from synthetic Evidence Models
  (no filesystem needed — purity payoff).
- `tests/test_meta_contracts.py` — one planted violation per contract in fixture
  repositories (tmp dirs with synthetic registers/artifacts); asserts the specific
  finding fires and others don't.
- `tests/test_meta_manifest.py` / `tests/test_meta_assurance.py` — derivation correctness;
  byte-determinism (generate twice, compare bytes — enforces CT10).
- `tests/test_cli.py` additions — `audit` rc semantics (0/1/2).
- Real-repo integration: audit runs green on the actual registers at HEAD.

## 12. Research positioning (Phase 6)

After the audit first runs green, update RESEARCH_POSITIONING.md with an
evidence-mapped candidate table:

| Candidate | Supporting artifacts | Gaps |
|---|---|---|
| Evaluation Framework | *(filled from repo evidence at implementation time)* | |
| Evaluation Validation Platform | | |
| Evaluation Assurance Platform | | |
| Evaluation Reliability System | | |
| Evaluation Infrastructure | | |

The evidence and gap columns are deliberately not pre-written in this spec: filling them
before the audit exists would be exactly the opinion-first pattern v0.6 removes.

A recommendation is marked with its reasoning, but the README headline does not change
until the user approves the framing. The repository earns its identity from artifacts.

## 13. ADR-0006

"Meta-evaluation layer" ADR records: placement beside products (not Core); consumer-rule
status (one realized consumer + named future consumers); the deferred-generality decision
with its trigger (JudgeKit registers); the evidence-graph-as-internal-primitive direction
(influences architecture, not yet a public thesis).

## 14. Scope guards and non-goals

- No new scenarios (multi-hop stays deferred, on record in DATASET_AUDIT).
- No re-bench: audit is not a harness change; published numbers untouched.
- No dashboards, no visualization, no Neo4j, no JudgeKit implementation.
- No composite quality score (standing refusal).
- No generic evaluation abstraction before a second consumer exists.

## 15. Gate

Single gate-review document applying seven lenses inline (architecture, scientific,
research, product, technical debt, staff engineer, interview ROI) — each answering: what
became stronger, what assumptions remain, what should never be built, single next
milestone. Consistent with all prior gates: no multi-agent spawns. Conventional commits;
one gate review, then ship.
