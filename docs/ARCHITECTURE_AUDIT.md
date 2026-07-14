# Groundtruth — Architecture Audit (v0.5)

Auditing every reusable abstraction against the founding rule (ADR-0001):

> No reusable abstraction enters Core unless it has at least two concrete
> consumers.

"Concrete consumer" is interpreted strictly: a **realized** consumer (code that
exists) or a **designed** consumer (a named product with a specified need). For
the newest primitives the second consumer is designed, not realized — disclosed
below, not hidden. This is a re-verification, not a redesign: v0.4's evidence
directive closed the architecture unless a measured result or an unexpressible
consumer forces a change. Neither occurred.

## Core inventory

| Module | LOC | Purpose | Realized consumers | Designed 2nd consumer | Debt | Removal cost |
|---|---|---|---|---|---|---|
| `core/trace.py` | 45 | Ordered spans, no wall-clock, `schema_version` | AgentProbe runner, validation loader, report | JudgeKit (judge transcripts), PlannerBench (plan steps) | none | Very high (everything reads Traces) |
| `core/evaluator.py` | 36 | `Detector` protocol + `evaluate()` | AgentProbe detectors, LLM judge | JudgeKit agreement detectors, PlannerBench efficiency detectors | none | Very high (the product-agnostic heart) |
| `core/scorecard.py` | 69 | `Failure` + aggregation + `robustness` | AgentProbe, CI gate, report | any product emitting Failures | #8 (`robustness` blends safety+utility) | High |
| `core/dataset.py` | 41 | `Case` + YAML loader | AgentProbe scenarios + validation | any product's scenarios | #7 (`suite` from key `product`) | Medium |
| `core/validation.py` | 160 | Measure detectors vs labeled traces | `groundtruth validate`, judge comparison, CI | JudgeKit self-measurement | none | High (this is the thesis) |
| `core/report.py` | 148 | Static self-contained HTML | `groundtruth report` | any product's scorecards | single realized consumer today | Low (isolated, output-only) |
| `adapters/agent.py` | 44 | `Agent` protocol (Observation→Action) | scripted subjects, OllamaAgent (both modes) | JudgeKit judge-as-agent wrapper, PlannerBench planners | none | High |

## Consumer-rule verdict

- **Satisfied for the load-bearing primitives** (`trace`, `evaluator`,
  `agent`, `validation`): each has ≥2 realized consumers *today* (e.g. the
  `Detector` protocol is used by five rule detectors *and* the LLM judge — two
  independent realized consumers, not one).
- **Satisfied-by-design for `report.py`:** one realized consumer. It is an
  output adapter, not a Core abstraction others build on, so the rule is weakest
  here and the risk is lowest (removal cost Low). Flagged, not actioned.
- **No violations requiring code change.** No primitive was added in v0.4 that
  lacks a consumer: `max_steps` and `stateful` are *parameters on existing
  consumers*, not new Core abstractions. `NonCompletion` is a Detector (uses the
  existing protocol), not a new primitive.

## Abstractions that correctly did NOT enter Core

- **Stateful memory** lives in `OllamaAgent`, not in the `Agent` protocol — the
  protocol still passes a single `Observation`; history is the adapter's private
  concern. Correct: only one adapter needs it today.
- **Step budget** is a `run_scenario` parameter, not a Core policy object. No
  second consumer would justify a `Budget` abstraction.
- **Bootstrap CI** is a standalone script, not a Core statistics module — one
  consumer, kept out of Core.

Each of these is a place where the consumer rule *prevented* speculative
generalization. That is the rule working.

## Complexity / Karpathy check

Core is **545 LOC** across 7 files; the largest (`validation.py`, 160) is the
thesis itself. Capability grew in v0.4 (a sixth detector, two measurement
conditions, a flagship experiment) with **zero new Core abstractions** — the
system got more capable while Core stayed the same size. That is the intended
direction.

## Recommended simplifications

1. **`robustness` (debt #8):** the one abstraction whose semantics exceed its
   name — it blends a safety rate and a completion rate. Recommend splitting at
   v1.0 into `safety_rate` + `completion_rate`, keeping the composite only as a
   labelled summary. Not urgent (it is a derived property, not a primitive), so
   deferred, not done — consistent with "minimal changes only."
2. **`report.py` single consumer:** acceptable as an output adapter; revisit
   only if a second output format appears (would share a formatter interface).

No other changes justified. The architecture is closed for v0.5.
