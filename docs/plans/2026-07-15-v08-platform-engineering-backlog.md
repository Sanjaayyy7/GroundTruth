# v0.8 Platform Engineering Backlog — Repository Stewardship System (RESERVED)

**Status:** approved, deferred · **Reserved for:** v0.8 · **Recorded:** 2026-07-15

This is platform engineering debt intentionally deferred — not a nice-to-have
list. The ARB approved the architectural intent at the v0.6 review; v0.7 is
deliberately kept to a single scientific question (external validation), so
implementation of this subsystem is queued as the dedicated objective of v0.8.

## Governing question for v0.8

> Can Groundtruth preserve long-term repository quality, context efficiency,
> architectural consistency, and maintainability as the project scales?

(v0.7 answers exactly one different question: can the Meta-Evaluation Engine
audit an evaluation Groundtruth did not produce? Keeping the milestones
separate preserves one-hypothesis-per-version discipline.)

## Binding constraints (carry into v0.8 unchanged)

- **Advisory only.** The stewardship system never modifies, moves, renames,
  archives, or deletes repository content. It produces evidence-backed
  recommendations; a human (or an explicitly instructed session) acts on them.
- **Reports, not mutations.** Deterministic report artifacts; CI-integrable
  where a check is cheap and non-blocking.
- **No new abstractions.** Same rule as everywhere else in this repo
  (ADR-0001): no plugin systems, no service framework, no scheduler. Scripts
  and documents.
- **Never touches the measurement pipeline.** Stewardship reads; it does not
  sit between scenarios, runners, detectors, or the audit.

## The five services

1. **Repository Steward** (highest ROI). Detects duplicate files, abandoned
   prototypes, obsolete experiment outputs, stale generated artifacts,
   orphaned specs, unused utilities, broken references, inconsistent version
   strings, documentation drift. Every recommendation classified
   KEEP / MOVE / ARCHIVE / DELETE / IGNORE with explicit evidence.
2. **Context Optimizer.** Deterministic inventory of the repo from a
   context-window perspective: Essential Context / Supporting Context /
   Cold Storage / Generated Artifacts / Safe-to-Ignore, with relative
   context-cost estimates. Goal: cheaper agent sessions without losing
   engineering quality.
3. **Architectural Drift Monitor.** Cross-checks implementation ↔ ADRs ↔
   specs ↔ research docs ↔ README ↔ registers for semantic drift (renamed
   concepts, stale terminology, claims the docs no longer support). Natural
   sibling of the evidence audit: contracts police registers; this polices
   prose. Overlap with CT1–CT10 must be audited before building — anything
   the contracts already enforce is out of scope here.
4. **Technical Debt Auditor.** Structured debt register (extends SPEC.md §7)
   categorized Engineering / Architecture / Scientific / Research /
   Documentation / Product / Interview-ROI, each item scored for cost to fix,
   risk, expected information gain, expected interview gain.
5. **Release Readiness Auditor.** Pre-tag checklist runner: docs
   completeness, CI health, reproducibility, contracts, benchmark freshness,
   version coherence, licensing, generated artifacts, git cleanliness.
   Runs only before releases.

## Repository Constitution (companion document)

One governance document (not another README) defining how the repository may
evolve: when a new top-level directory is allowed; when an ADR is required;
Core admission criteria (restating ADR-0001); archival vs deletion policy;
generated-artifact vs source-of-truth ownership (e.g. `runs/` contents are
derived, registers are source); mandatory naming conventions; documentation
lifecycle (when a doc is obsolete); experiment permanence rules; what must
never be committed.

## Acceptance sketch for v0.8 (to be pre-registered then)

- Each service produces a deterministic report on the current repo with at
  least one true finding and no mutation.
- The Constitution exists and every service cites it as its rulebook.
- Zero changes to `groundtruth/` package code paths used by measurement.
- Success metric is six-months-out maintainability, not files changed.

## Explicitly out of scope (v0.8, restated from standing refusals)

Dashboards, web UI, APIs, plugin systems, always-on background agents,
auto-fixers of any kind.
