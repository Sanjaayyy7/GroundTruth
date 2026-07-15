# ADR-0006: Meta-evaluation layer — evidence model at the center, files at the edge

**Status:** accepted · **Date:** 2026-07-15

## Context
v0.5 produced the evidence artifacts (claims register, threats analysis,
detector-quality runs, reproduction log) but every consistency guarantee
between them was manual. v0.6 adds `groundtruth audit`: a subsystem that
constructs an auditable evidence model from those artifacts and derives
reproducible assessments. The ARB mandated one canonical internal model:

```
Evaluation Artifacts
        ↓
Evidence Loader (YAML/filesystem/git — the one concrete adapter)
        ↓
Evidence Model (EvidenceNode and typed nodes; no I/O)
        ↓
Evidence Graph (primary internal representation)
        ↓
Evaluation Contracts (pure invariants over the graph)
      ↙          ↘
Quality Manifest   Assurance Report   (siblings; neither imports the other)
```

## Decision
1. **Placement:** `groundtruth/meta/` sits beside `products/`, not inside
   `core/`. The consumer rule (ADR-0001) blocks Core entry until a second
   realized consumer exists. Today the engine has one realized consumer
   (the `groundtruth audit` CLI auditing this repository) and named future
   consumers (JudgeKit, PlannerBench, external evaluations emitting the same
   register formats).
2. **Files are adapters, the model is the architecture.** `loader.py` is the
   only module that performs I/O; it resolves every environmental fact (file
   existence, glob matches, metric-source values, git commit validity,
   version strings) into node attributes. Everything downstream — graph,
   contracts, manifest, assurance — is a pure function of the model.
3. **Exactly one loader.** No abstract base classes, no plugin system, no
   loader registry, no extension API. Room for future consumers lives in the
   versioned register **formats** (claims.yaml schema v2, threats.yaml
   schema v1), not in speculative Python interfaces.
   **Generalization trigger:** when JudgeKit's registers exist and show what
   a second consumer actually needs.
4. **Findings, never scores.** Contracts emit explanatory Finding objects —
   deliberate symmetry with the detector philosophy (ADR-0002). There is no
   composite quality score anywhere; the manifest reports dimensions
   separately, and dimension coverage is register-driven (`dimensions:` tags
   on claims/threats) so `meta/` contains no evaluation-specific node ids.
5. **Sibling assessments.** The manifest answers "what evidence exists?";
   the assurance report answers "what conclusions are justified?". Both
   derive from (graph, findings); neither imports the other.

## Rejected
- *Generic "evaluate any evaluation" abstraction layer now*: one realized
  consumer; ADR-0001 applies to the meta layer exactly as it applies to Core.
- *`health.py` / traffic-light status*: implies green/yellow/red; the output
  is per-conclusion assurance, not a grade.
- *Composite quality score*: a scalar would exceed the evidence — the same
  refusal, for the same reason, as per-scenario CIs at n=8.
- *Graph library / visualization / Neo4j*: plain dataclasses answer the
  provenance question; anything more is furniture.
- *`blocked_by` as a graph edge*: future experiments are free text today;
  the edge waits until experiments become registered nodes.

## Consequences
Every published claim is now machine-checked against its evidence at every
CI run (contracts CT1–CT9; CT10 byte-determinism enforced by tests). Drift
between prose, registers, metrics, and git state fails the build with a
named, explanatory finding. Cost: registers carry more structure
(threat_refs, metrics, preregistration, dimension tags) that authors must
maintain — the audit itself polices that structure.

Internal direction (not a public thesis): claims, threats, artifacts,
experiments, and versions are all views over one primitive — evidence. The
Evidence Model admits that ontology explicitly; future products should
consume it rather than invent parallel bookkeeping.

## Review trigger
When JudgeKit lands: revisit whether the loader generalizes (second register
family), whether `meta/` primitives move toward Core under the ≥2-consumer
rule, and whether future experiments should become registered nodes with
`blocked_by` edges.
