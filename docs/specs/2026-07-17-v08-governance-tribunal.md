# v0.8 Governance Tribunal — Final Pre-Implementation Review

**Mandate:** determine whether Repository Steward deserves permanent
existence inside Groundtruth. Posture: the architecture is guilty until
proven necessary. **Primary question:** if Repository Steward never
existed, would Groundtruth become objectively weaker in a measurable,
reproducible, long-term way?

**Method note.** The directive names 18 phases. They collapse into the 11
sections below because several phases interrogate the same evidence from
different angles (inevitability ≈ competitive benchmarking ≈ platform
boundary; first-principles reconstruction ≈ destructive simplification;
governance ≈ invariant taxonomy). Producing 18 parallel documents would be
the mega-report anti-pattern this repository has already refused. Phase →
section mapping: P1/P13 → §2; P2/P15 → §3; P3/P4 → §4; P5/P6 → §5;
P12 → §6; P7/P8/P10 → §7; P11 → §8; P17 → §9; P14/P16 → §10; P18 → §11.

## 1. New evidence gathered for this tribunal (main @ 2035c33)

Measurements that did not exist at convergence:

| Evidence | Measurement | Bears on |
|---|---|---|
| Documentation growth, v0.1 → v0.8c (8 milestones, 6 days) | 8,945 → 274,091 md bytes (**30.6×**); md now 1.66× py bytes; docs outgrew code from v0.5 onward | Reference surface compounds every milestone; RC2's problem recurs by construction |
| Top-level directory additions | 5 new top-level entries across 8 milestones (`runs`,`validation` v0.2; `.github`,`docs` v0.3; `experiments` v0.5; `examples` v0.7) — none declared anywhere | RC1's problem recurs ~every other milestone |
| Derived-artifact churn | 11 of 41 commits (27%) touched `runs/` — each one a staleness opportunity; one realized defect (debt #17, negative-control-proven) | RC4 recurrence |
| Version-anchor co-change history | 4/4 commits touching `pyproject.toml` also touched README; **zero historical RC3-class violations** | RC3 is the weakest-evidenced contract (see §8) |
| **Debt-register drift at HEAD — live true positives** | #13 marked "v0.4 — detector + label…" but `non_completion` shipped in v0.4 (detector + `tests/test_non_completion.py` exist); #11 says "stateful re-bench pending" but 6 stateful scorecards exist in `runs/`; #12 timing reads "v0.4", still open at v0.8 (no ruff config, no `py.typed` — verified) | RC7 has ≥2 measurable findings **today**; the prose table is drifting right now, not hypothetically |
| Archaeology probe | git log messages name every milestone (v0.1–v0.8 all greppable), but SPEC's roadmap records only 2 commit hashes (the v0.7 prereg pair); milestone→commit lineage otherwise lives outside the repo | Gap real; remedy is one SPEC column, **not** steward scope (§11 R6) |

The debt-drift finding materially changes the tribunal's posture: the
convergence report conceded the repo might be clean at HEAD. It is not.
A six-day-old, single-author, unusually disciplined repository has already
accumulated register drift that no existing mechanism can detect.

## 2. Inevitability adjudication, per component (P1, P13)

Columns: capability lost if removed / best external replacement /
uniqueness that survives JudgeKit → PlannerBench → 5 products → 10
contributors / verdict.

| Component | Lost if removed | External replacement | Uniqueness under scale | Verdict |
|---|---|---|---|---|
| Constitution | The declaration source; every RC becomes unparameterized opinion | None — no tool reads project-specific law | Strengthens: more products = more roles/freezes to declare; mechanism constant | **Inevitable.** The one component every other depends on |
| Inventory + repo manifest | Role coverage becomes unauditable; onboarding artifact disappears | `git ls-files` lists paths, assigns no meaning | Grows more valuable per contributor (the map is for people who didn't draw it) | Inevitable given RC1 |
| RC1 role coverage | New top-level entries land undeclared (measured: 5 in 8 milestones) | None constitution-coupled | Scale increases undeclared-entry rate | Keep |
| RC2 reference integrity | 274 KB of living prose stays unpoliced; drift detected only by readers | lychee/markdown-link-check: partial — no lifecycle classes, no evaluation-root resolution (both FP modes measured), no unified findings | 10 contributors multiply reference-creation rate; FP budget is the pressure point (trigger exists) | Keep |
| RC3 version coherence | Anchor drift possible | CT6 covers 2 anchors already | **Zero historical violations; 4/4 co-changes clean.** Weakest contract | Keep provisionally — cheapest check; explicit retirement trigger added (§11 R5) |
| RC4 freshness declarations + CI diff | Debt #17 class stays open — one realized defect, 27% commit exposure | CI `git diff --exit-code` does the diff (adopted); nothing checks declarations exist | More products = more derived artifacts | Keep (split honestly recorded: the diff is CI's, not steward's) |
| RC5 import layering | ADR-0001's core law stays unenforced (verified: no test) | import-linter: partial — config-file rules, no Constitution, non-diff-friendly output | Every product multiplies edges; also guarantees steward's own deletability (§9) | Keep |
| RC6 ADR liveness | Future ADRs may ship without review triggers | None | Constant | **Keep, halved** — its reference-resolution half duplicated RC2 (§3); shrinks to trigger-presence only (§11 R1) |
| RC7 debt integrity | Prose debt keeps drifting — **2 live findings at HEAD** | Issue trackers: external state, not evidence-linked, unavailable offline | Contributors multiply debt entries | Keep — now the best-evidenced contract |
| RC8 freeze integrity | MiniJudge (validation evidence for claim C11) mutable without objection | Branch protection: no remote; path-scoped protection doesn't exist in git | More frozen consumers accumulate (each ships one) | Keep |
| CLI verb | Demo + human invocation | `python -m` invocation | Constant (~20 lines) | Keep — house pattern, trivial cost |
| Findings model + report generator | Committed byte-deterministic evidence artifacts | pytest output: not committed, not byte-stable, not diffable evidence | The committed report IS the product under the thesis | Keep (see §3 — this was the tribunal's closest call) |
| Debt register (`docs/debt.yaml`) | RC7 has nothing verifiable to police | SPEC §7 table — measured drifting | Constant | Keep; SPEC §7 becomes a pointer, not a mirror (§11 R4) |
| CI integration | Enforcement becomes optional → unenforced prose, the measured failure state | — | Constant | Keep, blocking (Law 10 provides legal exits) |
| Read-only git layer | Steward loses all repository facts | — | Constant | Keep; determinism hardening required (§11 R2) |
| Constitution schema (v1, 6 keys) | Declarations become free-form → unparseable | — | The one real lock-in surface (§9) | Keep, capped, versioned |

## 3. First-principles reconstruction and destructive simplification (P2, P15)

**Reconstruction.** Ignore the architecture; smallest system answering
EQ1–EQ6: one declarations block + one pytest module (~250 lines) asserting
RC1–RC8; findings = assertion messages; CI = existing pytest step. No
steward package, no CLI verb, no manifest, no report, no findings model.

Honest comparison (the tribunal's closest call):

| Dimension | pytest-only | steward module |
|---|---|---|
| Modules / concepts / commands | 1 / ~3 / 0 | 5–6 / ~8 / 1 |
| Lines incl. tests | ~250 | ~750 budget |
| Enforcement of EQ1–EQ6 | **Equivalent** | Equivalent |
| Committed evidence artifacts | None — pytest output is transient and not byte-stable | Manifest + report, committed, diffable |
| Finding citations | Assertion strings | Structured findings, file/line/commit |
| Reflexive thesis ("repo audited like an AI system") | Absent — a lint suite | Present — same mechanics as the audit |

Adjudication: enforcement alone does not decide this — pytest wins on
size. The decision turns on what Groundtruth *is*: the audit's committed
artifacts (`runs/quality-manifest.json`, assurance report) are the
product, and tests only guard them. If the steward's output is transient
test noise, v0.8's thesis ("the repository becomes auditable with the
rigor applied to AI systems") is not implemented — it is approximated.
The ~500-line delta buys the committed evidence chain, which is the
milestone. **Module retained.** Recorded as the strongest reduction the
tribunal rejected, with the size budget (≤2× meta/'s 748 lines, tests
included) as the enforceable price of that rejection.

**Deletion pass results** (everything was attempted):

| Deletion attempted | Outcome |
|---|---|
| RC6's reference-resolution half | **DIES** — duplicate of RC2 (found by this pass) |
| SPEC §7 as prose mirror of debt.yaml | **DIES** — pointer only; mirror = duplicate truth, and §1 proves prose tables drift |
| RC3 | Survives, barely — zero-violation history vs. near-zero cost; retirement trigger attached instead |
| Manifest OR report (keep one) | Survives — manifest is the inventory (RC1's evidence), report is the findings (RC2–RC8's evidence); different consumers, no overlap |
| CLI verb | Survives — 20 lines, house pattern |
| Separate `model.py` | Deferred to implementation — file count is not law; the size budget is |
| Constitution | Survives — removing it reverts every check to hardcoded opinion |
| CI step | Survives — optional enforcement is the measured failure state (§1) |

## 4. Entropy and duplicate truth (P3, P4)

Where entropy measurably accumulates (from §1): documentation mass (30.6×
in 8 milestones), derived artifacts (27% commit churn), top-level
structure (5 undeclared additions), register state (2 live drift
findings). Code entropy is comparatively controlled (py bytes grew 8.4×,
sub-linear to docs).

Duplicate-truth inventory at HEAD:

| Duplication | Class | Policed? |
|---|---|---|
| claims.yaml ↔ CLAIMS.md; threats.yaml ↔ THREATS_TO_VALIDITY.md | Required redundancy (machine + prose) | Yes — CT8 |
| pyproject version ↔ README banner | Required redundancy | Yes — CT6 |
| Committed manifests ↔ regenerable outputs | Derived artifact | **No — debt #17** (closes via RC4/CI) |
| SPEC §2 architecture table ↔ package layout | Documentation convenience | No; RC5 covers the import subset; residue accepted as JUDGMENT |
| SPEC §7 ↔ future debt.yaml | Would-be config duplication | Pre-empted: pointer only (§11 R4) |
| README v0.7 narrative ↔ ADR-0007 | Human convenience | No; accepted — narratives cite, don't restate law |
| v0.7 completion report | Kept **outside** repo deliberately | Correct avoidance — and evidence for the observer-effect threat (§6) |

Verdict: the steward **reduces** entropy where it is measurably
accumulating (references, state, structure, freshness) at the price of
one bounded new entropy source (a 6-key versioned schema). Net direction
is measured, not asserted: four growing surfaces gain checks; one small
fixed surface is added.

## 5. Governance model and invariant taxonomy (P5, P6)

Every Constitution law carries: **origin** (ADR or milestone) ·
**rationale** (one sentence) · **enforcement** (RC# or JUDGMENT) ·
**amendment** (edit + justification in the same commit; architectural
laws additionally require an ADR) · **retirement trigger** (named
condition; a law without one is incomplete and RC-checkable as such —
the Constitution's own schema enforces the fields' presence).

Roles (current reality, single maintainer): maintainer proposes; ARB
(gate review) accepts; future contributors propose via PR + ADR. Evidence
required to amend: a finding, a falsified prediction, or a fired review
trigger — never preference. Law classes: **permanent** (advisory-only;
never weaken a check to silence a finding — identity-level, amendment
requires an ADR with a named replacement mechanism) vs **experimental**
(all RC scopes, until three milestones of service each).

Invariant taxonomy — every enforced invariant in the repository and its
owner:

| Invariant class | Instances | Owner | Gaps/overlaps |
|---|---|---|---|
| Scientific/evidence | CT1–CT10 (registers ↔ artifacts ↔ git) | `meta/` | None; register-scoped by design |
| Published metrics | Snapshot regression tests (micro P/R/F1 pins) | pytest | Corpus freeze after publication only partially covered — recorded as RC9 candidate, **not built** (§11 R7) |
| Harness purity | No-consumer-literal guardrail tests | pytest | None |
| Determinism | CT10 + byte-parity tests | `meta/` + pytest | Steward inherits the same obligation |
| Version | CT6 (2 anchors) | `meta/` | RC3 supersets at repo level; CT6 retained for external consumers — required redundancy, documented |
| Repository structure/reference/state/freshness/freeze/layering/debt | RC1–RC8 | steward (proposed) | The previously ownerless class — §1 shows it drifting |

## 6. Scientific review — threats to the steward's own validity (P12)

| Threat | Evidence | Mitigation | Residual uncertainty / experiment | Retirement |
|---|---|---|---|---|
| Construct: 8 invariants ≠ "repository quality" | Standing limitation, mirrored from audit ("consistency, not truth"): a declared-but-foolish role rule passes RC1 | Published limitation; JUDGMENT laws stay human | Unknown unknowns in invariant space; RC9+ evidence bar is the discovery mechanism | Never — permanent epistemic limit |
| Internal: negative controls only cover imagined violations | v0.6/v0.7 precedent: controls caught real leaks anyway | 8 pre-registered controls, one per RC | First uncaught real violation = the experiment; protocol predicts candidates | — |
| External: single repo, single author (steward's own E6) | All evidence in §1 is from this repo | Scope claim: "this repository," zero generality (ADR-0008) | Second repository adopting steward = the discharge experiment | Reopens ADR-0008 |
| **Observer effect: blocking law pushes work outside the repo** | **Already observed once**: v0.7 completion report deliberately kept out-of-repo to avoid drift law | Exemption mechanism gives a legal in-repo path; exemption-creep counter (§11 R3) makes avoidance visible | Does declared friction change commit behavior? Longitudinal: exemption count + out-of-repo artifact census per milestone | — |
| Instrumentation drift: git output not byte-stable across machines | `core.quotePath`, locale affect `ls-files` encoding | Pin invocation: `git -c core.quotePath=false`, `-z`/NUL where applicable, `LC_ALL=C` (§11 R2) | Cross-machine CI vs local parity test | — |
| False negatives: conservative RC2 scope misses prose refs | Chosen deliberately (two measured FP modes) | Documented trade; scope widens only with FP budget evidence | Count missed-drift incidents post-ship | — |
| Longitudinal: exemption creep hollows the law | Analogy: lint-suppression rot in industry practice | R3 counter + trigger (≥5 active or any >2 milestones old → review) | — | — |
| Institutional: single maintainer = governance theater risk (ARB and maintainer are the same person's sessions) | True today | Honest disclosure; the mechanism (committed evidence, prereg ordering, D10) is what outlives the arrangement | First external contributor tests it | — |

## 7. Evolution, resilience, archaeology (P7, P8, P10)

Scenario sweep (which contracts move):

| Scenario | Effect on RC1–RC8 |
|---|---|
| A AgentProbe-only (today) | All function; RC3 near-idle (§8) |
| B JudgeKit | Declaration edits only (new roles, new derived artifacts); mechanism unchanged — this is the design's test and its point |
| C PlannerBench | Same as B; RC8 list likely grows (each product may ship a frozen consumer) |
| D Five products | RC1 rule list ~doubles; single-file Constitution still fine at ~50 rules; **first pressure**: RC2 corpus size → runtime (mitigant: checks are O(files), no network) |
| E Twenty contributors | RC2 FP budget is the bottleneck (trigger exists); blocking-CI decision must be revisited (ADR-0008 trigger already names this) |
| F Open-source community | Exemption governance becomes the contested surface; R3 counter is the instrument |
| G/H Academic / lab adoption | Steward stays repo-local by design; adoption pressure would fire the generality trigger (second repository) |
| Unexpectedly critical | RC8: the moment any published claim depends on a frozen artifact tree, freeze integrity is the difference between "validation evidence" and "mutable example" |

Resilience: no CI → CLI verb runs locally, findings unchanged (CI is
transport, not brain). Shallow/absent git history → rc 2 usage error,
never silent wrong findings (v0.7's fetch-depth lesson pre-applied).
Corrupted Constitution → parse failure = rc 2, blocks on error visibly;
single point of failure accepted and tested. History rewrite → RC8/RC7
commit references dangle loudly (correct behavior: the evidence chain IS
broken). Release pressure → Law 10's two exits, both auditable.

Archaeology (P7): a 2029 maintainer can reconstruct decisions (8 ADRs),
experiments (dated specs/plans + committed prereg ordering), and versions
(git log carries v0.1–v0.8 strings — verified). The one measured gap:
milestone→commit lineage is not tabulated in-repo. Remedy: one column in
SPEC §5 (§11 R6). Explicitly not steward scope — a documentation edit,
not a subsystem.

## 8. Failure economics per contract (P11)

Qualitative; cost = maintenance + review + CI + false-positive burden,
value = §1 evidence weight:

| RC | Lifetime cost | Evidence weight | Net |
|---|---|---|---|
| RC1 | Low (glob match) + declaration friction | Recurs ~every 2 milestones | Positive |
| RC2 | **Highest** (extraction scope, FP budget) | 274 KB growing surface; 2 FP modes pre-measured | Positive, watched — the contract most likely to need scope surgery |
| RC3 | Near-zero | **Zero historical violations** | Marginal — kept only because cost ≈ 0; retirement trigger attached (R5) |
| RC4 | Near-zero (declaration check; diff is CI's) | One realized defect; 27% exposure | Strongly positive |
| RC5 | Low (AST walk) | Core law of ADR-0001, unenforced 8 milestones | Strongly positive |
| RC6 (halved) | Near-zero | 8/8 ADRs comply; locks invariant for ADR-0009+ | Positive, small |
| RC7 | Low + migration cost (one-time) | **2 live findings at HEAD** | Strongly positive — best evidenced |
| RC8 | Near-zero (tree-hash compare) | Protects C11's validation evidence | Strongly positive |

No contract has negative net value; RC3 is the closest and carries its
death condition.

## 9. Reversibility (P17)

| Decision | Class |
|---|---|
| Steward module | **Fully reversible** — RC5's own law ("nothing imports steward except cli") is a structural deletability guarantee; removal = delete directory + one CLI verb + one CI step |
| Blocking CI | Fully reversible (one workflow line) |
| debt.yaml migration | Reversible (regenerate a table); pointer-not-mirror keeps SPEC intact |
| Constitution file | Reversible (laws revert to unenforced prose — the current state) |
| Declarations schema v1 + artifact paths | **The lock-in surface** — format law once published (ADR-0007 D2 discipline: versioned schema, migration note on change). Accepted knowingly; capped at 6 keys |
| RC identities | Partially reversible — retiring a fired contract is cheap; retiring one people rely on is a governance event (by design) |

The architecture's deepest reversibility property: the layer that audits
the repository can be removed from the repository without touching the
science. The reverse (meta/ removal) is not true. Hierarchy correct.

## 10. The case against, rebutted; interview signal (P14, P16)

**Steelman (strongest honest form):** "This is a ~750-line bespoke lint
suite for a single-author repo with 30 markdown files, zero broken links,
and zero TODOs. Every gap is hypothetical at n=1 author; discipline got
you here and generic tools cover the rest. The interview value is already
banked in the convergence and tribunal documents — keep the ADRs, skip
the code. Governance for a solo repo is theater."

Rebuttals, all from measurement:

1. *"Discipline suffices"* — discipline demonstrably failed twice under
   maximum discipline conditions: debt #17 (stale manifest passes CI,
   negative-control-proven) and the v0.6 shallow-checkout bug that would
   have broken the first public CI run. Both latent despite TDD, gate
   reviews, and prereg.
2. *"Gaps are hypothetical"* — §1: two live RC7 findings at HEAD, in a
   six-day-old repo. Drift is present tense.
3. *"Generic tools cover it"* — adjudicated per-component in §2; the one
   place external tooling fully wins (RC4's diff) was already conceded
   to CI. 6 of 8 contracts are constitution-coupled with no external
   reader.
4. *"n=1 author"* — correct, conceded, registered as the steward's E6
   analog (§6) with scope claim limited accordingly. An honest scope
   limit is not an argument for zero enforcement inside that scope.
5. *"Value already banked in documents"* — partially TRUE, conceded: if
   implementation never happens, most career ROI survives in the review
   chain. But a documented-then-unbuilt governance layer is precisely
   the "dead experiment / speculative folder" pattern the Constitution
   outlaws — shipping the documents without the checks would plant the
   first violation of the law being written. The concession therefore
   argues for building small, not for not building.

Interview signal ranking (artifacts, strongest first): (1) the
convergence report's eight rejections; (2) this tribunal's rejected
reduction (§3 — arguing *against* one's own module and losing on
evidence); (3) ADR-0008's reopen triggers; (4) the live RC8 demo;
(5) the code itself. Competencies made observable: systems thinking,
scientific method applied reflexively, complexity rejection, governance
design, decision reversibility. The signal is durable because it is in
the git history's ordering, not in prose claims.

## 11. Verdict (P18)

**PROCEED WITH TARGETED REVISIONS.** Not "proceed unchanged" — the
tribunal drew blood, which is the evidence it was real:

- **R1** RC6 halved: trigger-presence only; reference resolution belongs
  to RC2 (duplicate found in §3).
- **R2** Read-only git layer pins byte-determinism:
  `-c core.quotePath=false`, NUL-delimited output, `LC_ALL=C`.
- **R3** Exemption-creep instrument: report lists active exemption count
  + age; review trigger at ≥5 active or any older than 2 milestones.
- **R4** SPEC §7 becomes a pointer to `docs/debt.yaml` at migration — no
  prose mirror (prose state tables measurably drift: §1).
- **R5** RC3 carries an explicit retirement trigger: three consecutive
  silent milestones → demote into RC4's declaration check or retire.
- **R6** Milestone→commit lineage column added to SPEC §5 at next SPEC
  touch — documentation fix, explicitly outside steward scope.
- **R7** RC9 candidate (validation-corpus freeze after metric
  publication) recorded with the standard evidence bar; not built.

Alternatives rejected: *proceed unchanged* (R1/R2/R4 are real defects
found by this review), *reduce further* (the only substantive reduction —
pytest-only — was adjudicated and rejected on the thesis test, §3, with
the size budget as the enforceable price), *return to convergence* (no
structural finding invalidated the single-subsystem shape; every §11
revision fits inside it), *abandon* (§10: the steelman's strongest point
concedes enforcement value and two families of measured defects that
discipline alone did not catch).

Answer to the primary question: **yes — measurably.** Without the
steward: debt state drifts (drifting now), ADR-0001 stays unenforced
(8 milestones and counting), frozen validation evidence stays mutable,
committed evidence can go stale silently (happened once), and 274 KB of
compounding prose stays unpoliced. Each is a measurement, not a
conviction.

Implementation may begin: pre-registered protocol first (readiness review
§5 ordering, amended by R1–R5), then TDD. Size budget ≤ 2× `meta/`
(≈1,500 lines including tests) is law; exceeding it fires ADR-0008's
falsification trigger.
