# ADR-0002: Detectors return explanatory Failures, never scores

**Status:** accepted · **Date:** 2026-07-11

## Context
Mainstream eval libraries reduce evaluation to a number ("score = 72") or a
boolean. A number tells you *that* a system failed, not *why*, and cannot be
acted on by the engineer who has to fix it.

## Decision
The atomic output of every detector is a structured `Failure`:
`(case_id, detector, category, severity, summary, causal chain, recommendation)`.
Scorecards aggregate Failures; they never replace them.

## Rejected
- *Numeric metrics as the primitive*: cheap to emit, useless to act on;
  competing on metric count is DeepEval's game and a losing one.
- *Rich ontology now* (confidence, root-cause, evidence sub-objects):
  rule-based detectors have no confidence semantics — a confidence field
  today would be fabricated precision. Revisit when LLM-judge detectors
  (which emit real confidence) exist.

## Consequences
Detectors are harder to write — each must explain itself. That cost is the
product.

## Review trigger
First LLM-judge detector: reconsider `confidence` and evidence references,
with the labeled validation set measuring whether they are calibrated.
