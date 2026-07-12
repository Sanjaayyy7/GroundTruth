# ADR-0005: v0.3 = CI gate + benchmark expansion; dashboard demoted; re-architecture rejected

**Status:** accepted · **Date:** 2026-07-12

## Context
Post-v0.2 architecture gate review. Candidates for v0.3: React dashboard
(inherited roadmap), grand re-architecture ("subject generalization",
taxonomy expansion, full version matrix), CI integration, benchmark
expansion, developer experience, JudgeKit start.

## Decision
v0.3 ships: (1) `groundtruth ci` — scorecard vs stored baseline, nonzero
exit on regression, GitHub Action template, and this repo gating itself
publicly; (2) benchmark expansion — more local models × more scenario
families, published comparative table; (3) a static self-contained HTML
report generator in place of a React dashboard; (4) `schema_version` on
persisted Trace/Scorecard JSON (stored CI baselines are its first real
consumer); (5) debt items: LICENSE, cwd-independent paths, label-vocabulary
guard, demo agents moved under the product.

## Rejected
- *React dashboard now*: commodity engineering, weakest differentiation per
  hour; a solo project cannot out-UI funded observability companies.
- *Re-architecture*: core is already subject-generic (audit evidence:
  `Trace.subject` is an opaque string; nothing agent-specific in core);
  proposed new fields had <2 consumers — fails ADR-0001.
- *JudgeKit now*: the platform proof, but splitting focus before AgentProbe
  is undeniably deep weakens both stories. Scheduled v0.4.

## Review trigger
End of v0.3: if the benchmark table lands and the CI gate works, JudgeKit
starts; if scenario realism became the bottleneck, trace-ingestion mode
("bring your own trace") jumps the queue.
