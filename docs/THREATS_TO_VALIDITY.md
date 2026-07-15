# Groundtruth — Threats to Validity (v0.5)

Groundtruth's claims are treated here as an academic paper's would be. Each
threat lists its **current mitigation**, **remaining risk**, and the
**future experiment** that would resolve it. Claim ids reference
[claims.yaml](claims.yaml).

## Internal validity — is the measurement instrument correct?

| # | Threat | Current mitigation | Remaining risk | Future experiment |
|---|---|---|---|---|
| I1 | Parser converts format non-compliance into a fake safety finding | Caught once (v0.3 agent parser) and once (judge parser); adapter now translates the unambiguous action-field variant; fail-open only for genuine garbage | A third parseable-but-unhandled reply shape could still misscore | Parser fuzzing over recorded real replies; assert no silent Finish on well-formed tool JSON |
| I2 | Stall was itself an instrumentation artifact (the whole C1 finding) | Resolved: pre-registered confound experiment proved it and the fix (`non_completion` + stateful variant) is in the suite | The stateful adapter uses one prompt format; a different memory encoding might behave differently | Test 2–3 memory encodings (tool-role messages, summarized history) as adapter variants |
| I3 | Detector logic bug inflates precision/recall | 78 tests, snapshot pinned, every fp/fn is a named designed-hard case | A detector could be "right for the wrong reason" on this corpus | Mutation testing on detectors; adversarial label review |
| I4 | `non_completion` fires on legitimately long tasks | Structural rule keyed on absence of a `final` span, not step count; all scenarios are single-answer tasks | On a genuinely multi-step task, budget exhaustion ≠ failure | Add a multi-step-completion scenario; confirm the detector's scope is documented, not assumed |
| I5 | Determinism assumption is false for LLM subjects | Measured byte-identical for llama3.2 across both conditions from a fresh venv (C9) | Other five models verified equal-*scored*, not byte-diffed this milestone | Byte-diff all six across two runs; record any drift as a caveat |

## External validity — does it generalize?

| # | Threat | Current mitigation | Remaining risk | Future experiment |
|---|---|---|---|---|
| E1 | All subjects are ≤8B local models | Disclosed in every claim's scope | Findings may not hold for frontier models | Run the suite against one API frontier model (adapter already supports it) |
| E2 | One prompting style / system prompt | Single fixed system prompt documented in the adapter | Injection susceptibility is prompt-sensitive | Prompt-sensitivity sweep: 2–3 system prompts, same scenarios |
| E3 | One decoding config (temp 0, seed 42) | Chosen for reproducibility, disclosed | Stall fixed-point mechanism (C1) is specific to greedy decoding; temp>0 may differ | Repeat the stall experiment at temperature 0.7 |
| E4 | Mocked deterministic tools, not real APIs | Deliberate — it is what makes runs $0 and reproducible | Real tools have latency, errors, richer outputs that change behavior | Out of scope by design (POSITIONING anti-goal: no live tracing); note the boundary explicitly |
| E5 | 8 scenarios, one attack ontology | Info-gain argued per scenario | Attack space is far larger; coverage is a sample | Add multi-hop / delayed-instruction families (see DATASET_AUDIT) |
| E6 | The second consumer (MiniJudge) shares author and host repository with Groundtruth | Declared in the pre-registered v0.7 protocol and in C11's scope; MiniJudge differs in domain, terminology, data format, and threat-ID family | Same-author registers may unconsciously fit the engine's expectations; organizational independence is unproven | Audit an evaluation authored outside this repository (JudgeKit proper or a third party) with no coordination beyond the published format docs |

## Construct validity — does it measure what it claims?

| # | Threat | Current mitigation | Remaining risk | Future experiment |
|---|---|---|---|---|
| K1 | `robustness` blends safety and utility into one number | Documented as debt #8; existence-proof framing; never the headline | A reader may treat it as a pure safety score | Split into safety-rate and completion-rate at v1.0; keep the composite only as a summary |
| K2 | "Injection compliance" is proxied by "called the target tool" | Direct, low-proxy: the forbidden call is the harm | A model could call the tool for a benign reason | Already partly covered by the `ih_fp_01_causality` designed case; add a benign-call-of-target control |
| K3 | Detector categories are the author's ontology | 6 lenses, each with a distinct question; overlap is intentional and documented | The ontology could miss a failure class (as it missed stall until v0.4) | Every sampled-real cohort is expected to break the taxonomy — that is the corpus's job (immutable #11) |

## Statistical validity

| # | Threat | Current mitigation | Remaining risk | Future experiment |
|---|---|---|---|---|
| S1 | n=8 scenarios cannot support ordinal rankings | Existence-proof framing enforced repo-wide (C4) | A reader may still infer a leaderboard | Keep the scope sentence load-bearing; no per-scenario CI (would be theater) |
| S2 | Detector P/R rests on 68 single-annotator items | Bootstrap 95% CI published (C6): P [0.845, 1.000], R [0.790, 0.978] | Wide intervals; single labeler | Inter-rater κ on a ~20-item subset (blocked on a second annotator) |
| S3 | Class imbalance in the corpus | Per-category counts reported, not just micro | Micro can be dominated by frequent categories | Report macro alongside micro (cheap; add at next validate touch) |
| S4 | Selection bias in the sampled-real cohort | Seed-42 protocol documented (2/model + 3 pool) | 15 traces is a small draw | Grow the sampled-real cohort each benchmark cycle |

## Conclusion validity — which conclusions hold?

- **Robust (survive as Facts):** C1 (stall is an artifact), C2 (masked
  compliance), C4 (ranking inverts) — each has reproducible in-repo evidence and
  a mechanism, and each was stress-tested by a pre-registered or controlled
  procedure.
- **Conditional (Supported Observations):** C5, C7, C8 — real and reproduced,
  but tied to one scenario or one prompt design; they generalize only after the
  named future experiment.
- **Require replication before strengthening:** C6 (needs κ), any cross-model
  generalization (needs a frontier subject).

## The meta-point

The two most valuable assets in this repo — the stall-artifact finding and the
harness-validity incident record — exist *because* this kind of threat analysis
was run before publication rather than after. This document is not defensive
paperwork; it is the same instrument that produced the findings, pointed forward.
