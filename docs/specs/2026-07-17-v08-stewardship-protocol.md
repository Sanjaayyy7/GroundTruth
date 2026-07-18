# v0.8 Repository Stewardship — Pre-registered Protocol

**Committed before implementation.** This commit's SHA is the predictions
commit for the milestone; the ship commit is the results commit. Governing
inputs: architecture review report, stewardship architecture, ADR-0008,
implementation readiness review (all 2026-07-16), governance tribunal
(2026-07-17, verdict PROCEED WITH TARGETED REVISIONS R1–R7). Revisions
R1–R5 are folded into this protocol; R6 executes at this milestone's SPEC
touch; R7 is recorded, not built.

## The single scientific question

Can the repository's six measured, currently-unenforced invariants
(EQ1–EQ6) be enforced by an advisory, read-only, byte-deterministic layer
using the same declarations-in / findings-out mechanics that audit the
evaluation registers — without mutation, scores, schema growth, or a
false-positive rate that forces exemption creep?

## Hypotheses

- **H1 (alternative):** the eight repository contracts (RC1–RC8, as
  amended by R1: RC6 is trigger-presence only) are implementable
  stdlib-only, read-only, within ≤2× `meta/`'s measured size (748 lines →
  budget **1,496 lines including tests**), such that all eight planted
  violations produce named findings, artifacts are byte-identical across
  consecutive runs, declarations cover 100% of the tracked index, and at
  most 2 exemptions are needed at ship.
- **H0 (null):** enforcement requires any of: mutation, a git verb outside
  the enumerated surface, a seventh declarations-schema key, budget
  breach, or >2 forced exemptions in the first milestone — i.e. the
  converged architecture understated the real cost of repository law.

Both outcomes are publishable. H0 confirmation fires ADR-0008's
falsification trigger and the rollback path below.

## Architectural invariants exercised (frozen by architecture §10)

1. Constitution declarations block schema v1 — exactly 6 keys
   (`constitution_schema`, `roles`, `version_anchors`,
   `derived_artifacts`, `frozen`, `layer_rules`) plus `exemptions`;
   versioned under ADR-0007 D2 format-law discipline.
2. `docs/debt.yaml` schema v1 — id, title, category, state
   (open/resolved/accepted), origin version, evidence paths, resolution
   reference; **no numeric scoring fields**.
3. Steward artifact paths: `runs/steward/repo-manifest.json`,
   `runs/steward/steward-report.md`.
4. CLI verb `groundtruth steward`, rc 0 (no findings) / 1 (findings) /
   2 (declaration or usage error) — mirrors `audit`.
5. Import law (RC5 polices it, including on the steward itself):
   `steward` imports stdlib only; nothing imports `steward` except
   `cli.py`.
6. Subprocess surface (exhaustive): `git ls-files`, `git rev-parse`,
   `git cat-file`, `git diff --name-only`, `git log --format=%H -n1 --
   <path>` — all invoked with R2 determinism pins
   (`-c core.quotePath=false`, NUL-delimited output where applicable,
   `LC_ALL=C` in the subprocess environment).

## Success criteria (all required — replaces the rescinded "≥1 true finding")

1. **Eight negative controls caught:** each planted violation below is
   rejected with a named finding citing check id + path (or rc 2 where
   the plant corrupts declarations themselves).
2. **Zero mutations:** the steward writes only its two declared artifact
   paths; the working tree is otherwise untouched by a run — enforced by
   test.
3. **Byte determinism:** two consecutive runs on the same commit produce
   byte-identical manifest and report (CT10-parity test).
4. **Total coverage:** declarations match 100% of the tracked index; RC1's
   rule list ends in a catch-none; any unmatched path is a finding.
5. **Budget law:** `groundtruth/steward/*.py` + its test files ≤ 1,496
   lines, enforced by a test that counts them — exceeding the budget is a
   red test, not a judgment call.
6. **CI:** steward step runs after both audit steps, blocking; the debt
   #17 diff (`git diff --exit-code runs/ examples/minijudge/runs/`) ships
   in the same CI change.
7. An honest zero: a first full run with **no true findings at HEAD is a
   valid passing outcome**. Manufacturing a finding to pass this gate is
   the corruption the platform exists to detect.

## Failure criteria (any one confirms H0)

- Any RC check requires mutation or a subprocess verb outside §invariants-6.
- The declarations block needs a seventh schema key.
- The size budget is exceeded (fires ADR-0008's falsification trigger).
- More than 2 exemptions are forced in this milestone (RC2 scope defect —
  redesign trigger from the readiness review, not a licence to widen).
- Any negative control passes silently.
- Byte parity fails across consecutive runs on any machine in CI or local.

## Predicted findings (pre-registered, before any code exists)

1. **Migration exposes three stale SPEC §7 entries** (measured at HEAD by
   the tribunal): #13 timing reads "v0.4 — detector + label…" but
   `non_completion` shipped in v0.4 (`tests/test_non_completion.py`
   exists; 2 references in `detectors.py`); #11 reads "stateful re-bench
   pending" while 6 stateful scorecards sit in `runs/`; #12 timing reads
   "v0.4" and is still open at v0.8 (no lint config, no `py.typed`).
   These are recorded as evidence-cited state corrections in `docs/debt.yaml`
   during migration — not silently rewritten.
2. **First full steward run after complete declarations: rc 0.** The
   repo's reference/link surface measured clean on 2026-07-16; the known
   drift is register state, which the migration itself resolves. If the
   run instead finds something real, it is reported as an unpredicted
   true positive — the stronger outcome.
3. **Exemptions at ship: 0–2**, drawn from the two RC2 false-positive
   modes already observed live (evaluation-root path resolution;
   historical-lifecycle documents) — both designed around in architecture
   §6, so the prediction is zero, with 2 as the tolerated ceiling.

## Negative controls (one per contract; executed as tests, not history)

| RC | Planted violation |
|---|---|
| RC1 | A tracked file matching no role rule |
| RC2 | A broken relative link in a living document |
| RC3 | One declared version anchor desynced from the others |
| RC4 | A declared derived artifact with its regeneration command removed |
| RC5 | A forbidden import edge (e.g. steward importing core) |
| RC6 | An accepted ADR with its review-trigger line stripped (R1 scope: trigger presence only) |
| RC7 | A resolved debt item citing a resolution reference absent from git |
| RC8 | One byte edited inside the frozen `examples/minijudge/` tree |

Mechanism: controls run against fixture trees / temporary git
repositories in the test suite (v0.6/v0.7 invalid-variant pattern), so the
repository's own history stays clean. Every control must fail with a
named finding before ship; a control that passes is a blocking defect.

## Deterministic guarantees

Sorted iteration everywhere; no wall-clock timestamps; no absolute paths;
LF newlines; findings ordered by (check id, path, line); R2 git pins as
enumerated above. Manifest and report are pure functions of
(declarations × tracked content × declared commits).

## Permitted adaptations (declared now, not negotiated later)

- CLI-surface parameterization (`--root`, `--out`, `--json`).
- Declaration contents: role rules, anchors, derived artifacts, freezes,
  layer rules, debt entries — declarations are data, not architecture.
- Module file layout within `groundtruth/steward/` (tribunal §3: file
  count is not law; the budget is).
- Test-fixture design for the negative controls.
- Report prose wording — never its ordering or determinism rules.

## Forbidden adaptations (each is H0 evidence if "needed")

Mutation or auto-fix of any kind; scores, ranks, grades, health
percentages; session/token telemetry; NLP or semantic similarity; new
subprocess verbs; schema keys beyond v1; weakening or deleting a check to
silence a finding (Law 10 — the two legal exits are fix the repository or
amend the Constitution with justification in the same commit); prediction
language in any output.

## Redesign and review triggers

- **RC2 scope surgery** (not deletion): >2 forced exemptions this
  milestone.
- **R3 exemption-creep instrument** (standing): report lists active
  exemption count and age; review fires at ≥5 active or any exemption
  older than 2 milestones.
- **R5 RC3 retirement**: three consecutive silent milestones → demote to
  RC4's declaration check or retire.
- **Budget breach** → ADR-0008 falsification trigger (review, not
  silent acceptance).

## Rollback conditions

If H0 is confirmed and no permitted adaptation resolves it: delete
`groundtruth/steward/`, the CLI verb, and the CI step (tribunal §9 — the
import law makes this structurally guaranteed); keep the Constitution as
prose; record the outcome in the validation report. A failed experiment
is reported, never disguised.

## CI requirements

1. Steward step after both audit steps; blocking; rc semantics as above.
2. `git diff --exit-code runs/ examples/minijudge/runs/` after the audit
   steps and after the steward regenerates its own artifacts (debt #17's
   fix — the highest-ROI line in the v0.8 backlog, honestly recorded as a
   CI line, not steward code).

## Required evidence at completion

- Committed `runs/steward/repo-manifest.json` + `steward-report.md`,
  regenerated and diffed in CI.
- `docs/CONSTITUTION.md`: prose laws each naming an RC or marked
  JUDGMENT, one embedded YAML declarations block (schema v1).
- `docs/debt.yaml` with the three predicted state corrections cited to
  evidence; SPEC §7 reduced to a pointer (R4 — no prose mirror).
- SPEC §5 gains the milestone→commit lineage column (R6 — this
  milestone's SPEC touch is the trigger).
- Test suite: eight negative controls, byte-parity test, zero-mutation
  test, budget test, layering test (RC5 also enforced by pytest so the
  law holds even when the steward itself is the patient).
- Steward validation report (`docs/specs/…-v08-steward-validation-report.md`)
  with measured results, control outcomes, assumptions confirmed/rejected,
  debt created/retired, gate review, recommendation.

## Interview demonstration (design frozen)

`groundtruth steward` → rc 0 → edit one byte inside `examples/minijudge/`
→ named RC8 finding, rc 1 → revert → rc 0. "The repository that audits AI
evaluations audits itself with the same mechanics."

## Known limitations (published, not solved)

- The steward checks **consistency, not wisdom**: a declared-but-foolish
  role rule passes RC1 (standing limitation, mirrored from the audit).
- Single repository, single author — the steward's own E6 analog; scope
  claim is "this repository," zero generality (ADR-0008).
- Observer effect: a blocking law can push work outside the repo
  (observed once, v0.7 completion report); the R3 instrument makes
  avoidance visible rather than pretending it away.
- Conservative RC2 scope accepts false negatives by design; widening
  requires false-positive-budget evidence.
- Single-maintainer governance: ARB and maintainer are the same person's
  sessions; the mechanism (committed evidence, prereg ordering) is what
  outlives the arrangement.
