# Phase 10 Protocol — External Validation Pipeline (Pre-Registered)

**Date:** 2026-07-18
**Status:** REGISTERED before execution. No measurement has been taken at commit time.
**Milestone:** Phase 10 of Phase IV (External Validation & V1 Readiness)
**Mode:** MEASURE ONLY. No fixes, no redesign, no implementation during execution.

## 1. Hypothesis

**H-P10:** An external engineer with zero institutional memory, no access to prior
conversations, and no explanation from the author can — from a clean clone alone —
(a) understand what Groundtruth is, (b) reproduce its headline verification, and
(c) trace its headline claim to repository evidence, without assistance.

This protocol attempts to **falsify** H-P10, not confirm it.

## 2. Method

### 2.1 Clean-clone reproduction (instrumented)

1. `git clone` the local repo into an isolated scratch directory (no venv, no
   caches — clone state only; simulates a stranger's first clone).
2. Follow README instructions **verbatim, in document order**. No knowledge
   outside the README may be used to make a command succeed.
3. Log every command, its exit code, wall-clock time, and any deviation required.
4. First success = first README-promised verification that passes (tests green
   or CLI verification rc 0).

### 2.2 Persona walkthroughs (6, executed inline — no agent spawns)

Each persona is a scripted navigation trace with defined checkpoints. Personas:

| Persona | Budget proxy | Success criterion |
|---|---|---|
| Technical recruiter | README top screen (~first 40 lines) only | Can state what project is + one reason to trust it |
| Hiring manager | README full, 0 other files | Can name scope, maturity, and one measurable result |
| Staff AI engineer | ≤10 file opens | Can describe architecture + find one honest limitation |
| Applied AI engineer | README + commands only | Reaches a working run of the primary CLI verb |
| Research engineer | ≤6 hops from README | Traces headline claim → protocol → report → controls |
| OSS maintainer | Repo root + docs/ listing | Finds license, contribution path, CI definition |

### 2.3 Metrics recorded

Time-to-first-understanding (proxy: words/lines read before "what is this" is
answerable); time-to-first-success (wall clock of command sequence + command
count); first confusion point; first architectural misunderstanding risk; first
trust-building artifact; first unnecessary artifact; navigation dead ends;
duplicated information; evidence-chain completeness (hop count); README
sufficiency (count of undocumented steps); reproducibility friction (deviations
required); missing-context inventory.

### 2.4 Negative control for the method itself

The friction log must be capable of producing findings. Control: probe for
`CONTRIBUTING.md` and issue templates (believed absent). If the walkthrough
method fails to log absent-but-expected artifacts as friction, the method is
broken and the run is invalid.

## 3. Pre-Registered Predictions (locked before measurement)

- **P1:** Clean clone + README-verbatim setup reaches the full green test suite
  (168 collected; live-model tests auto-skip) with **zero undocumented steps**.
- **P2:** README top screen alone is sufficient for the recruiter persona
  (project identity + one trust artifact visible without scrolling past ~40 lines).
- **P3:** The run discovers **≥3 distinct friction points** (falsifies
  "publication-ready as-is"; if fewer, Phase 10 output is a pass certificate).
- **P4:** The headline v0.8 claim (steward H1 confirmed) is traceable from
  README to its validation report and negative controls in **≤3 hops**.
- **P5:** The OSS-maintainer persona fails at least one checkpoint
  (contribution path), because the repo has never been public.

## 4. Outcome Classes

- H-P10 **falsified** if: any README-verbatim command fails without documented
  recovery, OR any persona misses its success criterion, OR evidence-chain hops
  exceed budget.
- H-P10 **survives** only if all personas succeed within budget — in which case
  P3/P5 predictions were wrong and that is reported as such.

## 5. Deliverable

One report: `docs/specs/2026-07-18-p10-external-validation-report.md`.
Measurable observations only. Each finding cites file + line or command + rc.
Recommendations are listed but **not implemented** in Phase 10.

## 6. Threats to Validity (declared up front)

- Single evaluator; personas are simulated by the author's agent, not humans.
- Timing uses wall-clock for commands but reading-effort proxies (words, file
  opens, hops) for human comprehension — proxies, not human measurements.
- The evaluator has prior exposure to the repo; mitigated by verbatim-README
  discipline and hop budgets, not eliminated. Independent human replication
  remains future work and is the discharge condition for this phase's E6-class
  limitation.
