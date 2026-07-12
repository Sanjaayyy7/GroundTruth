# ADR-0001: One platform spine, and the ≥2-consumer rule

**Status:** accepted · **Date:** 2026-07-11

## Context
Groundtruth ships a family of evaluation products (AgentProbe, JudgeKit,
PlannerBench). The alternatives were three disconnected repos, or a
framework-first "generic eval platform" built before any product existed.

## Decision
Three-layer architecture: platform core (`groundtruth/core`, `groundtruth/adapters`)
→ products (`groundtruth/products/*`). Core never imports products. A primitive
may enter core **only when at least two named products consume it** (the
consumer table lives in SPEC.md §2).

## Rejected
- *Three separate repos*: no shared spine, three half-finished stories.
- *Framework-first genericity*: abstractions invented before consumers exist
  are guesses; every guess is maintenance debt.

## Consequences
Core stays small and provably necessary. Products absorb all domain
opinions. Cost: occasional friction when a primitive is "obviously" useful
but has only one consumer — it waits.

## Review trigger
When JudgeKit lands: audit whether any core primitive still has <2 real
consumers; demote it to product code if so.
