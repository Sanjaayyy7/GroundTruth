# ADR-0003: Deterministic, offline evaluation as the operating model

**Status:** accepted · **Date:** 2026-07-11

## Context
LLM-system evaluation is usually online (live APIs), non-reproducible, and
expensive. Reliability claims built on non-reproducible runs are anecdotes.

## Decision
Evaluation runs offline against deterministic mocked tools. Traces carry no
wall-clock timestamps. Scripted demo subjects (vulnerable / hardened /
paranoid) pin harness behavior byte-for-byte before any model is involved.
Real-model runs (Ollama, temperature 0, fixed seed) are *evidence
artifacts* stored in `runs/` — repeatable in practice, never treated as
regression fixtures.

## Rejected
- *Live-API evaluation first*: flaky, costly, and hides harness bugs behind
  model variance.
- *Pretending local inference is bit-deterministic*: it is not; the
  distinction between regression fixtures and evidence artifacts is the
  honest line.

## Consequences
Byte-identical re-runs make a CI regression gate possible (v0.3). Scenario
realism is bounded by the mocked-tool model — acknowledged limit.

## Review trigger
Multi-turn / stateful scenarios, or a trace-ingestion mode for external
frameworks, will strain the mocked-tool model — re-review then.
