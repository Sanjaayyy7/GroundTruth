# v0.8 Steward Validation Report

**Experimental objective** (protocol `2026-07-17-v08-stewardship-protocol.md`,
commit 12586d9): test H1 — RC1–RC8 implementable read-only, stdlib-only,
within 2× `meta/` (1,496 lines incl. tests), byte-deterministic, 100% index
coverage, ≤2 exemptions. Implementation lineage, one measurable step per
commit: 5d77ea7 model → b4b2637 loader → 69b2f88 inventory → ef1f203
checks+controls → 13ce99d report → 3f02bd0 Constitution+debt → 40c7d6c
blob-size fix → d09b5c5 CLI+artifacts → 742d611 CI. This report also
carries the constitutional mechanical validation, the steward
self-evaluation, and the scientific debt audit (three directive stages,
one document — the tribunal's anti-mega-report precedent).

## 1. Measured results — H1 CONFIRMED, no failure criterion fired

| Protocol criterion | Measured |
|---|---|
| 8 negative controls caught with named findings | 8/8 (`tests/test_steward_checks.py`, one per RC; plus only_importer variant) |
| Zero mutations | Enforced by test (full-tree byte snapshot before/after) |
| Byte determinism | Two-run parity test green; committed artifacts converge to a byte fixed point |
| 100% index coverage | 298/298 tracked paths matched; catch-none rule list; RC1 green |
| Size budget ≤1,496 | **1,185** (module 648 + tests 537; `meta/` = 748 + 365) — enforced by test, ADR-0008 trigger untripped |
| CI | Blocking steward step after both audits + `git diff --exit-code runs/ examples/minijudge/runs/` (debt #17 resolved: 742d611) |
| Honest zero | First full run at HEAD: **0 findings, 0 exemptions** (predicted outcome 2) |
| Exemptions ≤2 | **0** (predicted 0–2) |

Interview demo executed live, exactly as frozen in the protocol:
`groundtruth steward` rc 0 → one byte appended inside `examples/minijudge/`
→ `[RC8] examples/minijudge/README.md: frozen tree modified since
3d294a37356f`, rc 1 → revert → rc 0.

## 2. Predictions vs outcomes

| Pre-registered prediction | Outcome |
|---|---|
| Migration exposes stale #13, #11, #12 | **CONFIRMED**, all three — corrected in `docs/debt.yaml` with evidence (see register comments) |
| First full run rc 0 | **CONFIRMED** |
| Exemptions 0–2 from the two known RC2 FP modes | **CONFIRMED at 0** — both modes designed out (resolution order + lifecycle classes) |

**Unpredicted findings (the experiment's real yield):**

1. **Third RC2 false-positive mode**: template placeholders
   (`runs/experiments/stall-confounds-<date>/` in REPRODUCIBILITY.md).
   Fixed as a scope rule (glob/ellipsis/angle-bracket strings are
   templates, not references) with a red-green test — not an exemption.
2. **Manifest self-reference has no working-tree byte fixed point**: the
   manifest lists its own size; stat-based sizes oscillate. Fix 40c7d6c:
   sizes read from index blobs (`ls-files -s` + one
   `cat-file --batch-check`) — a pure function of the index.
3. **Live staleness incident, caught by the new guard within its first
   hour**: the CLI commit initially staged a manifest generated before two
   test files were tracked; the byte-freshness test failed, the artifact
   was regenerated and the commit amended. Debt #17's defect class
   reproduced itself *during the milestone that closes it* — the strongest
   evidence yet that this is a mechanism problem, not a discipline problem.

**Honest deviations, declared:** the git surface grew two flags within
already-enumerated verbs (`ls-files -s`, `cat-file --batch-check`); no new
verb. The zero-mutation guarantee is test-enforced rather than
capability-enforced (the steward could write anywhere; the test proves it
doesn't). Both recorded, neither fires a failure criterion as written.

## 3. Constitutional mechanical validation (ENFORCED / JUDGMENT)

Chain required per law: law → implementation → test → CI → evidence
artifact. CI runs pytest and `groundtruth steward`; evidence =
`runs/steward/steward-report.md` at HEAD plus the named test.

| Law | Class | Implementation → test |
|---|---|---|
| 1 advisory-only | **ENFORCED (by test)** | CLI writes only the out dir → `test_zero_mutation_outside_the_out_dir` |
| 2 role coverage | **ENFORCED** | `checks._rc1` → `test_rc1_control_unmatched_tracked_file` |
| 3 living references | **ENFORCED** | `checks._rc2` → RC2 control + template/FP tests |
| 4 version anchors | **ENFORCED** | `checks._rc3` → RC3 control |
| 5 derived artifacts | **ENFORCED** | `checks._rc4` + CI diff step → RC4 control + `test_committed_steward_artifacts_are_byte_fresh` |
| 6 import layering | **ENFORCED** | `checks._rc5` → three rule-kind controls + repo-green integration test (ADR-0001's core law mechanically enforced for the first time in 8 milestones) |
| 7 ADR triggers | **ENFORCED** | `checks._rc6` → RC6 control |
| 8 debt integrity | **ENFORCED** | `checks._rc7` → RC7 control |
| 9 freeze integrity | **ENFORCED** | `checks._rc8` → RC8 control + live demo |
| 10 never weaken | JUDGMENT | declared from origin; paper trail = exemption instrument |
| 11 no early abstraction | JUDGMENT | ADR-0001 discipline |
| 12 one hypothesis/milestone | JUDGMENT | gate-review discipline |
| 13 release procedure | JUDGMENT | checklist of existing commands |

No law required downgrade: every law claiming ENFORCED demonstrates its
full chain; the four JUDGMENT laws claimed nothing else from the start.

## 4. Steward self-evaluation (the evaluator evaluated)

- **False positives**: 3 modes observed across the milestone (2 predicted,
  1 discovered); all resolved by scope rules; FP count at HEAD: 0.
- **False negatives (accepted, documented)**: RC2 scans only markdown
  links + role-matching backtick strings in living docs — prose-only
  references escape it; RC3 covers 3 declared anchors; RC5 scans role
  `code` only (tests import the steward legally).
- **Redundant / permanently-green risk**: RC3 — zero historical
  violations, kept at near-zero cost with R5's retirement trigger armed
  (3 silent milestones → demote/retire). RC6 locks an invariant all 8
  current ADRs already satisfy; value accrues at ADR-0009+.
- **Noisy checks**: none observed (0 findings at HEAD).
- **Maintenance burden**: 1,185 lines vs meta/'s 1,113 incl. tests;
  largest single risk surface is the ~115-line flow-subset reader — the
  price of the stdlib-only law (a YAML import would violate RC5 on the
  steward itself; the reader is versioned format law instead).
- **Standing friction, accepted knowingly**: any commit that changes the
  index must regenerate steward artifacts (freshness test + CI diff make
  staleness loud). This is the enforcement mechanism, not overhead —
  readiness review §3 priced it in advance, and finding 3 above shows it
  firing correctly.

## 5. Scientific debt audit

Register entries #18–#21 added (`docs/debt.yaml`, RC7-policed). Classification:

| Debt | Severity | Cost | Career/publication value | Retirement |
|---|---|---|---|---|
| E6 — no externally authored consumer (threat register; debt #20) | Highest standing scientific limit | High (needs an outside party or JudgeKit-as-real-product) | Discharges "evaluation assurance platform" phrase | First external consumer audit green |
| Second-annotator κ (debt #19) | High for publication, low for engineering | Low (one annotator session) | Unlocks inter-rater claim in any writeup | κ measured on ~20-item subset |
| Multi-hop injection family (debt #21) | Medium | Medium (new scenario schema pressure) | Direct AI Agent Security competition relevance (~Sep) | Family shipped + measured |
| Steward regen friction (debt #18) | Low | Accepted | Demonstrates enforcement honesty | Permanent (mechanism) |
| Stateful benchmark confounds | Resolved v0.4 (experiment REPORT.md) | — | Already banked | — |
| Judge reliability scope | Scoped honestly (corpus v1, 4B/8B zero-shot) | — | Documented limit | Larger-judge rerun if ever claimed broader |
| Validation-corpus freeze post-publication | R7: RC9 candidate, **not built** | — | — | Earns RC status on a corpus-edit incident |

## 6. Gate review (five lenses) and recommendation

- **Architecture**: no assumption changed; the one adjustment
  (index-blob sizes) strengthened determinism. Nothing imports the
  steward but the CLI — deletability guarantee holds at HEAD, now
  mechanically checked.
- **Scientific**: H1 confirmed under pre-registered criteria; three
  unpredicted findings all strengthen the mechanism; the honest-zero
  outcome was allowed for and occurred.
- **Product**: the platform now audits its own repository with the same
  mechanics it sells — reflexive thesis implemented, not approximated
  (the tribunal's §3 adjudication vindicated).
- **Engineering**: complexity proportional (79% of budget, no new
  dependencies); debt net: one accepted item added (#18), one long-open
  item resolved (#17), three stale states corrected.
- **Career ROI**: newly verifiable by a hiring panel — a pre-registered
  protocol with confirmed/unpredicted findings separated; a constitution
  whose every ENFORCED law shows law→test→CI→evidence; a live 90-second
  demo; and a staleness incident caught by the mechanism it validates.

**Recommendation: SHIP v0.8** (version bump + README + SPEC lineage), then
Stage 7–9 of the master directive (public readiness, interview evidence
audit, v1 architecture freeze) — of which the first user-side action
remains the GitHub push that lets seven milestones of CI evidence run in
public.
