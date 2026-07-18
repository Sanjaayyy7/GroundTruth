# Groundtruth — Project Evolution

How the platform reached its current design: the decisions, the evidence that
forced them, and the ideas that were rejected. Every statement below is
traceable to a dated ADR, spec, or validation report in this repository.

## Why this exists

Groundtruth began (2026-07-11) from one observation: AI evaluation tooling
usually emits scores without explanations, and almost never measures the
quality of its own detectors. The founding commitments — one platform spine
with a family of products (ADR-0001), explanatory failures instead of scores
(ADR-0002), deterministic offline evaluation (ADR-0003), and measured detector
quality (ADR-0004) — were all recorded before the first benchmark ran, and all
four survived every subsequent gate unchanged.

## Version arc

| Version | Date | What shipped | Governing record |
|---|---|---|---|
| v0.1 | 07-11 | Platform spine + AgentProbe: schema, runner, 2 detectors, taxonomy, CLI | ADR-0001..0003 |
| v0.2 | 07-12 | 5-detector suite, Validation Engine, 53-item labeled set, first real LLM subjects | ADR-0004 |
| v0.3 | 07-12→13 | CI regression gate, 6-model benchmark | ADR-0005 |
| v0.4 | 07-13→14 | `non_completion` category, stall-confound experiment, stateful condition | `experiments/stall_confounds/` |
| v0.5 | 07-14 | Claims register, threats register, reproducibility + positioning docs | `docs/claims.yaml`, `docs/threats.yaml` |
| v0.6 | 07-14→15 | Meta-Evaluation Engine: evidence graph, ten contracts, derived assurance artifacts | ADR-0006 |
| v0.7 | 07-15 | Second-consumer validation (MiniJudge) — reuse tested, not asserted | ADR-0007, pre-registered protocol |
| v0.8 | 07-16→18 | Repository stewardship: Constitution, RC1–RC8, byte-deterministic committed evidence | ADR-0008, validation report |

## What the evidence overturned

The project's direction changed four times, each time because a measurement
contradicted a belief. These reversals are documented, not erased:

1. **The v0.3 leaderboard was wrong, and publishing it proved it.** Three
   models "won" at 0.875 by stalling until the step budget expired — behavior
   the five-detector taxonomy could not see. The v0.4 `non_completion`
   category made budget exhaustion visible and the ranking inverted: the
   former winners fell to 0.0, and the former last place (qwen3:4b) was
   untouched because its failures had always been real behavior. The old
   table remains in git history by design.
2. **"Stalling" was the harness's fault, not the models'.** A pre-registered
   confound experiment (`experiments/stall_confounds/PREDICTIONS.md`,
   committed before any run) attributed the stalls to stateless observation
   under temperature-0 decoding — a fixed-point machine. Given their own
   history, all 9 stalls vanished, and 2 of the 9 "safely stalled" models
   were revealed to comply with the injection instead. Conclusion recorded:
   stall is never resistance.
3. **Two measurement artifacts were caught by trace inspection before
   publication.** A strict parser scored two models' format deviation
   (`{"action": <tool>}`) as a safety property; the judge comparison's first
   pass reported 0 recall because judges answered `{"category": bool}` under
   `format=json`. Both were harness bugs producing result-shaped lies; both
   fixes and their lessons are in the README and the affected numbers were
   re-measured before publishing.
4. **A derived artifact cannot describe a tree that contains it.** The v0.8
   steward first computed manifest sizes from the working tree and never
   reached a byte fixed point (the manifest lists itself). Sizes now come
   from index blobs. Days later the freshness guard caught a genuinely stale
   manifest mid-commit — the failure class the design predicted, reproduced
   live during the milestone that closed it (debt #17).

## What was rejected, and why

- **React dashboard** — demoted at the v0.3 gate (ADR-0005): evidence value
  per hour lost to the CI gate and benchmark expansion.
- **Platform re-architecture** — rejected at the same gate: no failure
  evidence against the existing boundaries.
- **Composite quality score** — rejected permanently (v0.6): a scalar would
  exceed the evidence; the quality manifest reports per-dimension states.
- **A third product before a second consumer** — deferred until MiniJudge
  validated register reuse (ADR-0007); JudgeKit remains gated on that
  precedent.
- **PyYAML inside the steward** — rejected (v0.8): the steward enforces the
  repository's import-layering law and must not violate it to parse its own
  configuration; a ~115-line stdlib subset reader honors the format law.
- **RC9 (commit-message contract)** — recorded as a candidate, deliberately
  not built: no evidence yet that its absence causes failures.

## Why the current design

Every layer exists because a measurement demanded it: detectors are measured
because unmeasured detectors produced a false leaderboard; the meta-evaluation
engine exists because manual claim-document consistency drifted; the second
consumer exists because a reuse claim without a second consumer is an
assertion; the steward exists because the repository that publishes those
mechanics must survive them itself. The platform grew by discharge of specific
threats (each recorded in `docs/threats.yaml`), not by feature accretion.

## Where to verify

`docs/adr/` (8 decision records) · `docs/specs/` (dated protocols and
validation reports, pre-registration before implementation from v0.7 onward) ·
`docs/CONSTITUTION.md` (the thirteen repository laws) · `docs/debt.yaml`
(evidence-backed debt, including what remains open) · `runs/` (committed,
byte-deterministic evidence artifacts).
