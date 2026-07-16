# v0.8 Implementation Readiness Review — Repository Steward

**Inputs:** review report, stewardship architecture, ADR-0008 (all
2026-07-16). **Question:** may implementation begin?

## 1. Remaining architectural risks

| Risk | Severity | Containment |
|---|---|---|
| RC2 reference-extraction false positives block CI | Highest single risk | Both failure modes already observed and designed around (resolution order + lifecycle exemption, architecture §6); protocol must pre-register a false-positive budget (proposed: >2 exemptions forced in the first milestone = redesign trigger for RC2's scope) |
| Constitution declarations block becomes a second config language | Medium | Schema v1 capped at six keys (architecture §5); any new key requires the RC9+ evidence bar |
| Steward creep toward auto-fix / mutation | Medium | Enumerated read-only subprocess list; any other invocation is H0 evidence under the protocol; Law 1 |
| Blocking CI step turns advisory findings into forced decisions at bad times | Medium | Law 10 gives two legal exits (fix repo / amend Constitution with justification); exemptions are visible and diffable, so silencing has a paper trail |
| Finding-model duplication with `meta/` drifts into incompatible philosophies | Low | Deliberate, documented (ADR-0008 D5) with a named reopen trigger |

## 2. Scientific risks

- **A green first run proves nothing** (v0.6 lesson). The protocol must
  pre-register per-check negative controls: plant an unmatched tracked
  file (RC1), break a living-doc link (RC2), desync an anchor (RC3),
  remove a regeneration declaration (RC4), add a forbidden import (RC5),
  strip an ADR trigger (RC6), fake a debt resolution reference (RC7),
  edit one byte inside the frozen tree (RC8). Every control must fail
  with a named finding; steward artifacts must be byte-identical across
  runs (CT10-parity test).
- **Prediction discipline.** Like v0.7's seven pre-registered failure
  modes, the protocol should predict candidate first-run findings — and
  explicitly allow the honest outcome that the live repo yields zero true
  findings at HEAD (the 2026-07-16 scans found clean links and zero
  TODOs; this repo is currently well-kept). The backlog's "at least one
  true finding" acceptance criterion is therefore **rescinded as
  written** — manufacturing a finding to pass one's own gate is the exact
  corruption the platform exists to detect. Replacement criterion: every
  negative control caught + zero mutations + byte determinism +
  declarations covering 100% of the tracked index.
- **Steward checks consistency, not wisdom** (standing limitation,
  mirrored from the audit): a declared-but-foolish role rule passes RC1.
  Published as a limitation, not solved.

## 3. Maintenance risks

- Size budget: same order as `meta/` (~750 lines incl. tests). Exceeding
  ~2× that budget is itself a review trigger — the housekeeping layer must
  not outweigh the science it protects.
- Every new top-level dir / derived artifact / frozen path costs a
  declaration edit. This friction is the mechanism, but it is permanent;
  accepted knowingly.
- The declarations block is new format law → versioned schema, ADR-0007 D2
  documentation discipline, from day one.

## 4. Interview ROI assessment

- 90-second demo (composes with the v0.7 demo): `groundtruth steward` →
  rc 0 → edit one byte in `examples/minijudge/` → named RC8 finding, rc 1
  → revert → rc 0. "The repo that audits AI evaluations audits itself
  with the same mechanics."
- Question bank this milestone earns: why one subsystem instead of
  twelve (convergence report §2); why no scores; why the debt fix was a
  CI line and not a service (RC4 honesty); why the freeze check exists
  (protecting validation evidence); why blocking CI (Law 10); why no
  shared findings library (consumer rule applied against own convenience).
- The strongest artifact is the review report itself: documented
  rejection of eight of thirteen proposed subsystems is rarer interview
  evidence than any implementation.

## 5. Recommendation

**PROCEED**, in this order, one commit each, before any implementation:

1. Pre-registered protocol (`docs/specs/…-v08-stewardship-protocol.md`):
   H0/H1, success criteria (§2 replacement criterion), failure criteria,
   predicted findings, the eight negative controls, allowed adaptations
   (CLI surface, declaration contents), forbidden adaptations (mutation,
   scores, telemetry, NLP, new subprocess verbs, schema keys beyond v1),
   review trigger.
2. Then TDD implementation per the architecture doc, `meta/` conventions
   throughout.
3. Debt #17's CI diff ships in the same milestone (it is the highest-ROI
   line in the backlog and needs no steward code).

Structural objections outstanding: **none.** All five review lenses pass
with the containments above. The architecture survives its own gates
because most of what was proposed did not.
