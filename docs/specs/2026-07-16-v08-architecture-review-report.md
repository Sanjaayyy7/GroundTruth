# v0.8 Architecture Review Report — Repository Stewardship Convergence

**Phase:** pre-implementation architecture convergence. No code was written.
**Inputs treated as evidence, not authority:**
`docs/plans/2026-07-15-v08-platform-engineering-backlog.md` (5 proposed
services + Constitution) and the v0.8 master directive (12 proposed
subsystems). Nothing was grandfathered in; every proposal re-earned or lost
its existence below.

**Central question:** how should Groundtruth continuously evaluate the
quality, integrity, maintainability, and scientific health of its own
repository using the same evidence-first philosophy it applies to AI
systems?

## 1. Evidence base (measured on main @ a68c1c7, 2026-07-16)

| Fact | Measurement |
|---|---|
| Tracked files | 275 (`git ls-files`) |
| Tracked files that are pinned run evidence | 175 (64%) — `runs/` + `examples/minijudge/runs/` |
| Tracked markdown | 30 files, 239,130 bytes (≈60k tokens) |
| TODO/FIXME/XXX markers in tracked `*.py`/`*.md` | 0 |
| Existing debt register | SPEC.md §7 — 17 items, markdown table, not machine-verifiable |
| Register contracts | CT1–CT10 police `docs/claims.yaml` / `docs/threats.yaml` / prose threat doc / git facts — registers only |
| Version anchors mechanically checked | exactly 2 (CT6: pyproject + README regex) |
| Import-layering enforcement (ADR-0001 core law) | **none** — no test asserts core ↛ products (verified: no layering test in `tests/`) |
| MiniJudge freeze (ADR-0007) enforcement | **none** — declared in prose only |
| Committed-manifest staleness detection | **none** — debt #17, proven live by negative control (faked prereg commit passed CI silently) |
| Broken relative markdown links at HEAD | 0 (scan of all 30 files) |
| Dangling backtick path references at HEAD | 2 — both instructive, see §4 RC2 |

## 2. Method: questions before services

Per directive, no proposal was evaluated as a "service" first. Engineering
questions were derived from the evidence above; a service boundary was
allowed to emerge only where questions clustered on shared evidence and
shared output type.

### Engineering questions that survive (each traceable to a measured gap)

| # | Question | Observed gap it answers |
|---|---|---|
| EQ1 | Does every tracked file have a declared role and lifecycle? | No ownership/role declaration exists anywhere for 275 files |
| EQ2 | Do committed derived artifacts match what the code regenerates? | Debt #17 — stale manifest passes CI, demonstrated live |
| EQ3 | Do path/version references in living documents resolve? | Only registers are policed; 30 md files, 2 version anchors checked |
| EQ4 | Do the declared import-layer laws actually hold? | ADR-0001's central law has zero mechanical enforcement |
| EQ5 | Is the frozen validation consumer actually frozen? | ADR-0007 freezes MiniJudge in prose only |
| EQ6 | Is the debt register alive, evidence-backed, and never silently closed? | SPEC §7 "DONE v0.3p1" entries are unverifiable prose |

### Questions that do NOT survive

| Question | Why rejected |
|---|---|
| "Which files consume the most Claude attention / are repeatedly opened but never modified?" | Requires session telemetry that does not exist in repository evidence. Not reproducible from a checkout. Fails the Scientific gate (observation vs. opinion). |
| "How much context/token waste does the repo carry?" | Token estimates are heuristics, not observations. The deterministic residue (bytes per role class) falls out of EQ1's inventory for free. |
| "Has prose semantically drifted from implementation?" | Semantic similarity is a judgment, not a deterministic check. Any implementation would be an opinion engine — the exact thing the directive prohibits. The checkable subset (paths, versions, IDs, freezes) is EQ3/EQ4/EQ5. |
| "Is the repository release-ready?" | Decomposes entirely into existing checks (pytest, audit rc, CT6) plus EQ2/EQ3 — composition, not capability. See §5 verdict on Release Readiness Auditor. |

### The convergence observation

The six surviving questions share every field that would justify separate
subsystems:

- **Evidence consumed:** the git index, tracked file contents, and a set of
  declarations (roles, anchors, freezes, layer rules, debt) that today
  exist only as scattered prose.
- **Artifact produced:** deterministic findings citing file/line/commit.
- **Reasoning process:** pure function of (declarations × repository
  state); byte-deterministic, no network, no timestamps.
- **User:** the maintainer and future contributors; secondarily every
  agent session that reads the repo.
- **Frequency:** every push (CI) + on demand.
- **Permanent asset:** the declarations document (Constitution) and a
  machine-readable repository manifest.
- **Future consumers:** JudgeKit/PlannerBench milestones inherit the same
  checks unchanged; a release procedure reads the same findings.

When the differentiating fields are identical, the proposals are one
subsystem. That is the merge proof. **One service boundary emerges: a
Repository Steward = declarations (Constitution) + deterministic checks
(RC1–RC8) + one findings report.** Everything else below merges into it or
dies.

## 3. Verdicts — all thirteen proposals

| Proposal (source) | Verdict | Disposition |
|---|---|---|
| Repository Steward (backlog #1) | **KEEP — redesigned** | Becomes the single subsystem: inventory + RC checks + report. Loses the grab-bag "detect everything" framing. |
| Context Optimizer (backlog #2) | **REJECT as subsystem** | Telemetry-based metrics fail determinism; residue (bytes/files per role class) becomes two columns in the repo manifest. |
| Architectural Drift Monitor (backlog #3) | **MERGE — deterministic subset only** | Survives as RC5 (import layering), RC6 (ADR liveness), RC8 (freeze integrity). Semantic-drift detection rejected as opinion engine. |
| Technical Debt Auditor (backlog #4) | **REDESIGN** | No auditor service. SPEC §7 migrates to a machine-readable register (`docs/debt.yaml`) policed by RC7. Scoring fields (severity ranks, "interest accumulation") rejected — findings, never scores. Never auto-closed: trivially true, steward is advisory. |
| Release Readiness Auditor (backlog #5) | **MERGE** | Every checklist item maps to an existing check or an RC. Zero unique machinery remains → a documented release procedure in the Constitution, not code. Debt #17 closes as a CI diff step, which is where regeneration already happens. |
| Repository Constitution (backlog) | **KEEP** | The load-bearing deliverable: the declarations that make every RC checkable. One file, prose laws + one embedded machine-readable block. No companion YAML file — a second file is a duplicate-truth surface, the exact defect RC-class checks exist to catch. |
| Repository Evidence Registry (directive) | **REJECT** | The repo manifest + existing registers already enumerate all evidence. A third registry duplicates truth. |
| Repository Health Manifest (directive) | **MERGE** | *Is* the repo manifest (inventory output). "Health" framing rejected — implies a score. |
| Repository Assurance Report (directive) | **MERGE** | *Is* the steward findings report. Mirrors the assurance report's explanatory style; shares zero code with it. |
| Repository Findings Engine (directive) | **REJECT as shared abstraction** | A findings library shared by `meta/` and `steward/` would couple the scientific audit layer to housekeeping — a layering violation the steward itself would have to flag. Consumer rule (ADR-0001): `meta/`'s finding model already exists and serves its consumer; extracting it is a refactor of the scientific layer for the benefit of tooling. Steward carries its own ~20-line finding type; the duplication is deliberate and documented. Reopen at a third realized consumer. |
| Repository Contracts (directive) | **KEEP** | RC1–RC8, the heart of the subsystem. See §4. |
| Repository CLI (directive) | **MERGE** | One verb on the existing CLI (`groundtruth steward`), rc 0/1/2 mirroring `audit`. Precedent: `audit --name` (ADR-0007 D1) established the CLI as the legitimate consumer surface. |
| Repository Steward "predicts" (master directive: "observes, measures, reports, prioritizes **and predicts**") | **REJECT the word** | Prediction without a validated model is opinion. The steward observes and reports; humans predict. |

Thirteen proposals in; surviving: **one module, one constitution document,
one register migration, one CLI verb, one CI step.**

## 4. The eight repository contracts (RC1–RC8)

Each check exists because of a measured gap in §1 — none is speculative.
Full derivation fields shared across the suite are in §2; the
discriminating fields:

| ID | Check (deterministic) | Evidence consumed | Decision enabled | Why git/CI/pytest/lint can't already | Falsifier |
|---|---|---|---|---|---|
| RC1 | Every tracked path matches exactly one Constitution-declared role rule; no undeclared top-level entries | git index × role declarations | delete/archive/keep with citation; new-directory gating | Git tracks content, not purpose; no tool reads our role declarations | Role rules churn every milestone without catching anything |
| RC2 | Relative markdown links and repo-path references in **living** documents resolve | tracked md × lifecycle declarations | fix drift at the commit that causes it | Generic link checkers don't know our lifecycle classes or evaluation-root path resolution (both false-positive modes were observed live during this review: `runs/agreement.json` resolves against the MiniJudge root, not repo root; `tests/meta_fixtures.py` dangles only inside a historical plan doc that must stay immutable) | Sustained false-positive rate after scope fix |
| RC3 | All Constitution-declared version anchors agree (superset of CT6's two, incl. committed manifests' version fields) | anchor declarations × file contents | tag/release confidence | CT6 belongs to the *evaluation* audit and checks exactly 2 anchors | Anchors never disagree across 3 milestones AND RC4 subsumes the cases |
| RC4 | Every Constitution-declared derived artifact declares a regeneration command; CI diffs regenerated vs committed (`git diff --exit-code`) after the audit steps | derived-artifact declarations; CI recipe | trust committed evidence | This *is* achievable with existing tooling — the CI diff is debt #17's 2-line fix. The steward's share is only the declaration check. Recorded honestly: the highest-value item in the entire v0.8 backlog is a CI line, not a subsystem | Never fires after debt #17 closes |
| RC5 | AST-derived import graph satisfies declared layer rules (core ↛ products; nothing imports steward except cli; steward imports stdlib only) | Python sources × layer declarations | ADR-0001 enforcement; steward polices its own isolation | No layering test exists (verified §1); generic import-linter doesn't read the Constitution and isn't byte-deterministic in our report format | Graph never changes and rules never fire |
| RC6 | Every accepted ADR declares a review trigger; ADR path references resolve | docs/adr/* | ADR liveness; prevents dead decisions | Nothing checks ADR structure; ADR-0001–0007 all comply today — the check locks the invariant for ADR-0009+ | ADRs stop being written |
| RC7 | `docs/debt.yaml` schema-valid; every open item cites ≥1 existing evidence path; every resolved item cites a resolution reference that exists in git | debt register × git | debt triage with evidence; no silent closure | SPEC §7 prose table is unverifiable; no generic tool reads it | Register abandoned in favor of issues elsewhere |
| RC8 | Each Constitution-declared frozen path's git tree hash matches its declared freeze commit | freeze declarations × git trees | protects MiniJudge's value as validation evidence (ADR-0007: "frozen forever") | Git records changes; it does not *object* to them. Branch protection is unavailable (no remote) and path-scoped protection doesn't exist in plain git | A legitimate freeze amendment happens more often than an accidental edit |

## 5. Review gates — applied to the surviving subsystem

- **Architecture.** New capability: yes — six invariants currently
  enforced by nothing (§1). Reduces entropy: declarations turn implicit
  convention into checked law. Increases determinism: byte-deterministic
  outputs, sorted iteration, no timestamps (manifest.py conventions).
  No speculative abstraction: no shared findings lib, no plugin points, no
  generality for other repositories (single realized consumer: this repo —
  ADR-0001 applied to the steward itself). Could it disappear? RC4's CI
  diff and RC5 could survive as bare scripts; the other six checks would
  revert to unenforced prose — the measured state that produced debt #17.
- **Scientific.** Every finding cites file/line/commit; regeneration from
  a checkout is exact; no NLP, no similarity, no scores; every check has a
  plantable violation (negative control) by construction.
- **Engineering.** Read-only: subprocess surface limited to read-only git
  commands (`ls-files`, `rev-parse`, `cat-file`, `diff` — enumerated in
  the architecture doc). Maintenance estimate: same order as `meta/`
  (748 lines) including tests. Verifiability: any finding is re-derivable
  by hand from the citation.
- **Product.** In-thesis: the repository audits itself with the same
  contract mechanics that audit its evaluation evidence — the reflexive
  application of the AI-reliability thesis, recognizable as Groundtruth
  and not as generic repo tooling precisely because every check reads the
  Constitution.
- **Career ROI.** 90-second demo: `groundtruth steward` green → edit one
  byte inside `examples/minijudge/` → named RC8 finding, rc 1 → revert →
  green. Same mechanics as the audit demo, one layer up. Its absence keeps
  ADR-0001, ADR-0007's freeze, and evidence freshness unenforced — the
  weakness a Staff+ reviewer would find first.

## 6. Does stewardship belong inside Groundtruth at all?

Burden of proof on inclusion. Competing solutions, honestly:

| Check | Best external alternative | Verdict |
|---|---|---|
| RC2 | lychee / markdown-link-check | Partial substitute; loses lifecycle classes, evaluation-root resolution, unified findings, negative-control testability. Both observed false positives (§4) would be unfixable configuration fights |
| RC4 diff | plain CI `git diff --exit-code` | **External tooling wins — adopted.** The diff lives in CI; steward keeps only the declaration check |
| RC5 | import-linter | Partial substitute; config-file rules, non-Constitution, report format not diff-friendly |
| RC1, RC3, RC6, RC7, RC8 | none — all constitution-coupled | No generic tool reads our declarations |
| linting, formatting, coverage, tests | ruff / pytest / c8-style tools | **Not absorbed.** Explicit non-goal — existing tools own these |

Inclusion holds for the constitution-coupled checks; the one place
external tooling is strictly better (RC4's diff), external tooling is
used. That asymmetry is the evidence the decision is honest.

## 7. Result

The ideal outcome was inevitability, not coverage. Final shape:

1. `docs/CONSTITUTION.md` — laws (each naming its RC or marked JUDGMENT)
   + one embedded machine-readable declarations block.
2. `groundtruth/steward/` — inventory → RC1–RC8 → findings report;
   read-only; stdlib-only; byte-deterministic.
3. `docs/debt.yaml` — SPEC §7 migrated, policed by RC7.
4. `groundtruth steward` CLI verb, rc 0/1/2.
5. One CI step after the two audit steps, plus the debt #17 diff lines.

Each element removed leaves a measured gap from §1 open. Nothing in the
list exists because a directive named it; five of thirteen named proposals
survived, none intact.
