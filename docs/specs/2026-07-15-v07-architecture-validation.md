# v0.7 Architecture Validation Report — External Validation Outcome

**Protocol:** `docs/specs/2026-07-15-v07-external-validation-protocol.md`
(committed 074bfb3, before implementation).
**Results commit:** 3d294a3. **Verdict: H1 confirmed.** This document is the
milestone's gate review.

## Outcome, in one paragraph

The Meta-Evaluation Engine audited an evaluation Groundtruth did not
produce. MiniJudge (`examples/minijudge/`) — a real, deterministic, 12-item
judge-agreement evaluation with a script-generated metric artifact
(accuracy 0.75) — was authored to the published register formats and
audited green on the first run: 11 nodes / 11 edges, all contracts hold,
outputs byte-identical across runs. `git diff 074bfb3..3d294a3 --
groundtruth/meta/` is empty. The single adaptation was the pre-registered
CLI-surface change (`audit --name`). Eight negative controls each fail with
a named finding (CT1, CT2, CT4, CT5, CT7, CT8) or a register error (rc 2),
so the green audit is not vacuous. All evidence is enforced by
`tests/test_external_validation.py` (14 tests) and regenerated in CI on
every push.

## Success criteria — scorecard

| # | Criterion (protocol) | Result |
|---|---|---|
| 1 | Audit exits 0, all contracts hold, artifacts committed | PASS — `examples/minijudge/runs/` |
| 2 | Manifest identifies the consumer, not Groundtruth | PASS — `name: minijudge`, `version: 0.1.0` (required the `--name` flag) |
| 3 | Byte-determinism across runs | PASS — enforced by test |
| 4 | `meta/` diff vs protocol commit empty | PASS — 0 lines |
| 5 | No consumer literal in engine or CLI | PASS — enforced by test |
| 6 | ≥6 negative controls rejected with named findings | PASS — 8 controls |
| 7 | Second-consumer audit runs in CI | PASS — new workflow step |

## Assumptions register — predicted vs discovered

Pre-registered failure modes and what actually happened:

| # | Predicted assumption | Outcome |
|---|---|---|
| 1 | CLI hardcodes evaluation name | **Confirmed.** Only real defect found. Fixed at CLI surface; engine untouched. |
| 2 | Prose threat-doc path fixed at `docs/THREATS_TO_VALIDITY.md` | **Confirmed as convention.** Consumer complied; documented as format law (ADR-0007 D2), not generalized. |
| 3 | Threat-ID grammar `[IEKS]\d+ \| T\d+` implicit | **Confirmed as convention.** MiniJudge exercised the `T\d+` branch — first consumer ever to; grammar now documented. |
| 4 | Version anchoring assumes pyproject + README regex | **Confirmed as convention.** MiniJudge satisfied both; the non-Python-consumer question is documented, deliberately unsolved. |
| 5 | `_script_paths` skips `./.venv` tokens | **Held, harmless.** Documented. |
| 6 | Git facts assume `harness_commit` reachable from root | **Confirmed as convention.** Holds for in-repo consumers; documented. |
| 7 | Shallow CI checkout breaks CT6/D10 | **Confirmed latent v0.6 bug** — would have failed Groundtruth's own first public CI run. Fixed: `fetch-depth: 0`. |

Assumptions discovered during implementation that were NOT pre-registered:

| Discovery | Disposition |
|---|---|
| The manifest's D01–D10 dimension vocabulary is a fixed ontology; consumers either adopt its tags or report `gap` | Acceptable at n=2: MiniJudge tagged `detector_quality`, `label_quality`, `statistical_support` meaningfully; `gap` is an honest status, not an error. Revisit if an external consumer's quality dimensions don't map. |
| The assurance report's "Labeling needs" section keys on `attrs.annotators` | Worked unchanged for MiniJudge's T2 (annotators: 1) — evidence the register-driven design generalizes. |
| A consumer literal can leak through *help text* (first `--name` draft named MiniJudge in cli.py) | Caught by the guardrail test before commit — the v0.6 banned-words pattern paying off again. |

## What honestly limits this result

- **E6 (registered threat):** same author, same host repository. This
  validates architectural reuse of the formats and engine, not
  organizational independence. The registers were written by someone who
  knows the engine's expectations intimately; an outsider working only from
  format docs is the real test, and it has not happened yet.
- MiniJudge is small (2 claims, 3 threats). It exercises every contract
  but not scale.
- Contracts still check consistency, not truth (standing limitation from
  v0.6): a wrong-but-consistent MiniJudge would also pass.

## ARB checklist

- **Genuine second consumer?** Yes, with the E6 scope caveat: real
  computation, real registers, different domain/terminology/format/ID
  family — but same author and repo.
- **Which abstractions became stronger?** Register formats as the reuse
  surface (the core ADR-0006 bet) — now experimental fact. The
  register-driven dimension/labeling design (no Groundtruth literals in
  `meta/`) — carried a second consumer unchanged. Loader-resolves-
  everything purity — contracts/manifest/assurance needed nothing new.
- **Which became weaker?** None structurally. The fixed dimension
  vocabulary showed its edges (gap-status for untagged dimensions) without
  breaking.
- **Which assumptions survived unchanged?** One-loader/no-plugins;
  findings-never-scores; sibling manifest∥assurance; files-as-adapters.
- **Which failed?** Only the CLI's implicit "the evaluation is
  Groundtruth" default (fixed) and the shallow-CI assumption (fixed).
- **Any module redesigned?** No.
- **Should any module enter Core now?** No. Two audited register sets meet
  the ≥2-consumer letter, but not its spirit (independent product
  pressure); Core admission waits for JudgeKit proper (ADR-0007 D3).
- **Any ADR invalidated?** No. ADR-0006 strengthened; ADR-0001 discipline
  held (nothing generalized).
- **Architectural debt retired?** The unverified reuse claim — the largest
  standing IOU in the architecture docs. Plus the latent shallow-clone CI
  bug.
- **New technical debt?** Format conventions are now load-bearing and must
  stay documented (ADR-0007 D2); two register sets to migrate on any
  breaking format change; MiniJudge must be kept deliberately frozen.
- **Highest-information next milestone?** Scientific expansion (v0.8 was
  reserved for platform engineering by explicit directive; after it:
  multi-hop injection family + inter-rater κ per the ARB's v0.8+ guidance,
  and eventually an externally authored consumer to discharge E6).

## Interview-ROI review

What a hiring panel can now verify from the repository alone:

1. The architecture was designed under a one-consumer constraint with a
   named generalization trigger (ADR-0006, v0.6) — *before* any second
   consumer existed.
2. The reuse claim was then tested, not assumed: hypothesis, success and
   failure criteria, and seven predicted failure modes committed at
   074bfb3, demonstrably before the implementation at 3d294a3 — and the
   audit itself verifies that ordering mechanically (D10 ancestry check).
3. Generalization pressure was resisted on evidence: the only code change
   a second consumer forced was exposing an existing parameter; every
   discovered rigidity became documentation, not abstraction.
4. The demonstration polices itself: negative controls prove the green
   audit can fail, CI reproduces the result on every push, and the
   independence limitation is a registered threat (E6) with a named
   discharge experiment, not a footnote.

90-second demo (extends the v0.6 demo): `groundtruth audit --root
examples/minijudge --name minijudge` → all contracts hold; edit MiniJudge's
`value: 0.75` to `0.99` → named CT5 finding, exit 1; revert → green. Same
engine, different evaluation.

## Gate decision

v0.7 **ships**. H1 confirmed under the pre-registered protocol; the honest
scope of the result is recorded in C11's scope sentence, threat E6, and
this report. The phrase "evaluation assurance platform" remains unearned
until an externally authored consumer audits green.
