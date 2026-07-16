# ADR-0008: Repository stewardship as a single advisory layer

**Status:** accepted (architecture; implementation gated on pre-registered
protocol) · **Date:** 2026-07-16

## Context

After v0.7 the principal risk shifted from under-building to
over-building: everything added now becomes permanent platform spine. The
v0.8 backlog proposed five stewardship services plus a constitution; the
master directive proposed twelve subsystems. An architecture-convergence
review (`docs/specs/2026-07-16-v08-architecture-review-report.md`)
re-derived the milestone from engineering questions instead of service
names, against measured evidence: six repository invariants currently
enforced by nothing (no file-role declarations, stale-artifact blindness =
debt #17, unpoliced prose references, no import-layering test for
ADR-0001's core law, an unenforced MiniJudge freeze, an unverifiable debt
table).

## Decision

1. **One subsystem, not twelve.** `groundtruth/steward/` — declarations
   in, deterministic findings out. Components: Constitution loader,
   repository inventory, checks RC1–RC8, findings report. Five of
   thirteen named proposals survived, none intact; the rest merged or
   were rejected with evidence.
2. **Advisory and read-only, structurally.** The steward's subprocess
   surface is an enumerated list of read-only git commands. It evaluates
   the repository without becoming the repository — the same boundary the
   platform keeps toward the agents it evaluates.
3. **The Constitution is one file** (`docs/CONSTITUTION.md`): prose laws,
   each naming its enforcing check or marked JUDGMENT, plus one embedded
   machine-readable declarations block. No companion config file — a
   second file is a duplicate-truth surface.
4. **Checks earn existence from measured gaps only.** Each of RC1–RC8
   traces to an invariant verified unenforced on main @ a68c1c7. Adding
   RC9+ requires the same bar. Where existing tooling wins, it is used:
   debt #17's fix is a CI `git diff --exit-code`, not steward code.
5. **No shared findings abstraction with `meta/`.** The steward carries
   its own small finding model. Sharing would couple the scientific audit
   layer to housekeeping and refactor working science for the benefit of
   tooling; the consumer rule says the abstraction waits for a third
   realized consumer or demonstrated divergence pain.
6. **Findings, never scores; observation, never prediction.** No health
   grades, no debt "interest," no token estimates, no semantic-drift NLP.

## Rejected

- *Twelve-subsystem stewardship platform*: the proposals shared evidence
  source, output type, user, and cadence — the definition of one
  subsystem. Symmetry and conceptual completeness are not requirements;
  inevitability is.
- *Context Optimizer as a service*: its deterministic residue is two
  columns of the inventory; the rest (attention graphs, token waste,
  files-opened telemetry) is unmeasurable from a checkout and fails
  reproducibility.
- *Semantic drift detection*: judgment dressed as measurement. The
  checkable subset became RC5/RC6/RC8.
- *Composition of generic tools instead* (lychee, import-linter,
  pre-commit): partial coverage of RC2/RC5 only; nothing reads the
  Constitution; per-tool report formats break byte-determinism and the
  unified evidence style; negative-control testability is lost. The
  honest exception is recorded in Decision 4.
- *Stewardship outside the package* (scripts/, separate repo): CI and the
  CLI are the consumers; `meta/` set the precedent for a bounded
  non-Core layer inside the package. Isolation is enforced by RC5 itself.
- *Release Readiness Auditor as code*: decomposed entirely into existing
  commands; it survives as a Constitution checklist.

## Consequences

Six unenforced invariants become checked law; ADR-0001 and ADR-0007's
freeze gain mechanical teeth; the debt register becomes machine-verifiable;
committed evidence can no longer go silently stale (debt #17). Costs: the
Constitution's declarations block is new format law and must be versioned
and documented like the register formats (ADR-0007 D2 discipline); every
new top-level directory or derived artifact now requires a declaration
edit (friction by design); a small finding-model duplication between
`meta/` and `steward/` is carried knowingly; CI gains one blocking step
whose false-positive budget must be pre-registered.

## Review trigger

- A second repository wants the steward → generality review (until then,
  single-consumer, zero generality).
- The first external contributor era → revisit RC2 scope and the
  blocking-CI decision.
- Three consecutive milestones where steward findings are all false
  positives or all ignored → the subsystem's usefulness is falsified;
  demote to scripts or remove.
- A third consumer of the finding shape, or divergence pain between
  `meta/` and `steward/` models → reopen Decision 5.
