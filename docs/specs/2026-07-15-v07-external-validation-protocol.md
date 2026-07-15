# v0.7 External Validation — Pre-registered Protocol

**Committed before implementation.** This commit's SHA is the
`predictions_commit` for the resulting claim; the implementation commit will
be the `results_commit`, and D10 will verify ancestry mechanically.

## The single scientific question

Can the Meta-Evaluation Engine (v0.6: loader → evidence model → evidence
graph → contracts → manifest ∥ assurance) successfully audit an evaluation
that Groundtruth itself did not produce?

The architecture has claimed reuse since ADR-0006 ("future consumers:
JudgeKit / PlannerBench, external evaluations emitting the same formats").
That claim has never been tested. v0.7 exists solely to test it. The outcome
is binary and both outcomes are publishable.

## Hypotheses

- **H1 (alternative):** the engine is sufficiently evaluation-agnostic to
  audit a second, independently authored evaluation using only
  *register-level adaptation* — i.e. the consumer writes registers in the
  published formats (claims.yaml schema v2, threats.yaml schema v1, prose
  threat doc, version anchors) — with **zero modification to any module in
  `groundtruth/meta/`**.
- **H0 (null):** auditing a second consumer requires modifying engine
  modules, adding consumer-specific branches, or special-casing — i.e. the
  reuse claim was decorative.

**Adaptation boundary (declared now, not negotiated later):**
CLI-surface parameterization (exposing an argument the engine already
accepts) counts as register-level adaptation — the CLI is a consumer of the
engine, not the engine. Any edit to `meta/model.py`, `meta/loader.py`,
`meta/graph.py`, `meta/contracts.py`, `meta/manifest.py`,
`meta/assurance.py` counts as evidence toward H0 and requires the
four-question justification (what evidence revealed it; why v0.6 legitimately
lacked it; why a second consumer requires it; why future consumers should
inherit it).

## Second consumer design (smallest honest stressor)

**MiniJudge** — a miniature, real, executable judge-agreement evaluation
living at `examples/minijudge/`. Deliberately different from Groundtruth
where reasonable: different domain (judge agreement, not agent red-teaming),
different terminology (verdicts/agreement, not scorecards/robustness),
different threat-ID family (`T1…Tn`, exercising the second branch of the
loader's ID grammar), different claim-ID family (`J1…Jn`). It is NOT
JudgeKit and must not grow into it; it exists only to exercise the engine.

Constraints it must satisfy to be a fair test rather than a puppet:
- Its metric artifact is produced by a real deterministic script
  (`judge.py` over a committed labeled set), not hand-typed.
- Its registers make at least: one `fact` with machine-checkable metric
  provenance (CT5), one non-fact with a named confound (CT9), one
  preregistration-free claim set (D10 empty is a valid state), threats with
  mitigations/future experiments (CT7), bidirectional claim↔threat refs
  (CT4), a prose threat doc mirroring the register (CT8), version anchors
  (CT6).

**Known independence limitation, declared up front:** same author, same host
git repository. This validates *architectural* reuse (formats + engine), not
*organizational* independence. It will be registered as a new threat and
carried in the claim's scope sentence. Full independence waits for a
consumer authored outside this repo (JudgeKit proper or a third party).

## Success criteria (all required)

1. `groundtruth audit --root examples/minijudge …` exits 0; all contracts
   hold; a quality manifest and assurance report are generated for
   MiniJudge and committed.
2. Manifest correctly identifies the consumer (name, version, commit) — it
   must not claim to be Groundtruth.
3. Outputs are byte-deterministic across consecutive runs (CT10 parity).
4. `git diff <this commit>..<ship commit> -- groundtruth/meta/` is empty.
5. No consumer-specific literal appears in `groundtruth/meta/` or
   `groundtruth/cli.py` (enforced by a test, mirroring the v0.6
   banned-words pattern).
6. **Non-vacuousness:** ≥6 intentionally invalid variants of the consumer
   are each rejected with deterministic, named findings (or rc 2 for
   malformed registers): broken metric provenance, missing falsification,
   orphaned threat reference, missing evidence artifact, invalid status
   vocabulary, prose/register ID divergence, malformed YAML, missing
   register file.
7. The audit of the second consumer runs in CI alongside Groundtruth's own.

## Failure criteria (any one falsifies H1)

- Any `meta/` module requires modification to make the MiniJudge audit pass.
- Any conditional anywhere keyed on the consumer's identity.
- A negative-control register that the audit accepts (vacuous success).
- The consumer can only pass by copying Groundtruth's content (as opposed
  to its formats).

If H1 fails, the milestone still succeeds by documenting precisely which
assumption broke and why — architecture validation outranks preserving
previous design decisions.

## Predicted architectural failure modes (pre-registered)

Ranked by expected likelihood, from code inspection at protocol time:

1. **CLI hardcodes the evaluation name.** `_audit` calls
   `build_manifest(graph, findings)` leaving `evaluation_name="groundtruth"`
   — a second consumer's manifest would misidentify itself. Predicted fix
   class: CLI-surface parameterization (allowed adaptation).
2. **Prose threat-doc path is fixed.** Loader and CT8 assume
   `docs/THREATS_TO_VALIDITY.md` relative to root. Predicted outcome: the
   consumer complies with the convention; the path becomes a documented
   format requirement rather than a code change.
3. **Threat-ID grammar is implicit.** `_PROSE_THREAT_ID` accepts
   `[IEKS]\d+ | T\d+` only. MiniJudge deliberately uses `T\d+` to exercise
   the second branch; the grammar becomes documented format law.
4. **Version anchoring assumes Python packaging + README convention.**
   `pyproject.toml` `version = "…"` and README `**vX.Y — shipping**`.
   Predicted outcome: convention documented; non-Python consumers are a
   known open question, not solved speculatively now.
5. **Reproduce-command script scanning has Groundtruth habits.**
   `_script_paths` skips `./.venv`-prefixed tokens. Low impact; documented.
6. **Git-facts probing assumes the consumer root is inside a git history
   containing `harness_commit`.** Holds here (host repo); documented as part
   of the format contract.
7. **CI checkout is shallow** (`actions/checkout@v4` default depth 1), which
   would break CT6 commit-existence and D10 ancestry checks on the first
   real GitHub run — for Groundtruth's own audit too, not just MiniJudge's.
   Predicted fix: `fetch-depth: 0`. (Latent v0.6 bug surfaced by reviewing
   for v0.7; CI has never run remotely because no remote exists yet.)

## Required evidence at completion

- Committed MiniJudge artifacts (code, data, registers, runs).
- MiniJudge quality manifest + assurance report, regenerated in CI.
- `tests/test_external_validation.py` covering success criteria 1–6.
- Architectural validation report (`docs/specs/…-v07-architecture-validation.md`)
  with the assumptions register (predicted vs discovered vs survived), the
  ARB checklist answered, and the interview-ROI review.
- Registers updated: new claim (C11) with preregistration pair; new threat
  (E6, independence limitation) mirrored in prose.
- ADR only if evidence justifies one (expected: a short ADR recording what
  the second consumer proved and what it changed).

## What this milestone must NOT do

No JudgeKit, no PlannerBench, no abstract base classes, no plugin systems,
no provider registries, no generic evaluation interfaces, no dynamic
discovery, no dependency injection, no extension APIs, no
configuration-driven architecture. ADR-0001 and ADR-0006 remain binding.
Generalization is earned by realized consumers, and one new same-author
consumer earns documentation, not abstraction.
