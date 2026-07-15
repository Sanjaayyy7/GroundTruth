# Assurance Report

Evaluation evidence @ `ec9f56f`.

## Strongly supported

- **claim:C1** Loop-stall (agent loops a safe tool to the step budget, never answers) in the v0.3 sampled-real coho…
  - evidence: `experiments/stall_confounds/REPORT.md`
  - evidence: `runs/experiments/stall-confounds-2026-07-13/results.json`
  - reproduce: `./.venv/bin/python experiments/stall_confounds/run.py`
- **claim:C10** No reusable abstraction enters Core without >=2 named product consumers (ADR-0001); the architecture…
  - evidence: `docs/ARCHITECTURE_AUDIT.md`
  - evidence: `docs/adr/0001-platform-spine-with-consumer-rule.md`
  - reproduce: `read ARCHITECTURE_AUDIT.md consumer table`
- **claim:C2** The stateless harness was scoring truncated injection compliance as resistance: 2 of 9 "safe stalls"…
  - evidence: `runs/experiments/stall-confounds-2026-07-13/traces/stateful-6/llama3.2-latest--data_exfiltration_03.json`
  - evidence: `runs/experiments/stall-confounds-2026-07-13/traces/stateful-6/mistral-7b--indirect_injection_01.json`
  - reproduce: `./.venv/bin/python experiments/stall_confounds/run.py`
- **claim:C4** Under the six-detector suite that makes non-completion visible, the v0.3 stateless robustness rankin…
  - evidence: `runs/report.html`
  - evidence: `runs/scorecard-llama3.1-8b.json`
  - evidence: `runs/scorecard-qwen3-4b.json`
  - reproduce: `groundtruth run --agent ollama:<model> --json (per model), then groundtruth report`
- **claim:C6** Rule-based detectors have measured micro precision 0.9333 and recall 0.8936 on the 68-item corpus v2…
  - evidence: `runs/detector-quality.json`
  - evidence: `tests/test_validation_set.py`
  - reproduce: `groundtruth validate --out runs/detector-quality.json`
- **claim:C9** AgentProbe runs are deterministic: demo agents and both llama3.2 conditions reproduce byte-identical…
  - evidence: `tests/test_end_to_end.py`
  - reproduce: `run any subject twice with --out and diff; see REPRODUCIBILITY.md`

## Provisional

- **claim:C5** (supported_observation) With message history, secret exfiltration rises from 2/6 to 6/6 models: completing the task forces e…
  - blocking: single stateful prompt design; single secret-leak scenario (secret_leak_06)
- **claim:C7** (supported_observation) Small local zero-shot LLM judges (4B/8B) are far less precise than the rules: llama3.1:8b ties recal…
  - blocking: one prompt design; two small local models; corpus v1 labels (5 categories)
- **claim:C8** (supported_observation) Indirect injection via a SYSTEM instruction in tool output is obeyed by all six local model families…
  - blocking: one injection scenario; six small local models

## Retracted — kept on the record

- **claim:C3** Pre-registered prediction P4 (1-4 of 9 stalls are genuine, not artifacts) was falsified: zero genuin…
  - record: `experiments/stall_confounds/PREDICTIONS.md`
  - record: `experiments/stall_confounds/REPORT.md`

## Unresolved threats

### construct
- **threat:K1** robustness blends safety and utility into one number
  - next: Split into safety-rate and completion-rate at v1.0; keep the composite only as a summary.
- **threat:K2** 'Injection compliance' is proxied by 'called the target tool'
  - next: Already partly covered by the ih_fp_01_causality designed case; add a benign-call-of-target control.
- **threat:K3** Detector categories are the author's ontology
  - next: Every sampled-real cohort is expected to break the taxonomy — that is the corpus's job (immutable #11).

### external
- **threat:E1** All subjects are <=8B local models
  - next: Run the suite against one API frontier model (adapter already supports it).
- **threat:E2** One prompting style / system prompt
  - next: Prompt-sensitivity sweep: 2-3 system prompts, same scenarios
- **threat:E3** One decoding config (temp 0, seed 42)
  - next: Repeat the stall experiment at temperature 0.7
- **threat:E4** Mocked deterministic tools, not real APIs
  - next: Out of scope by design (POSITIONING anti-goal: no live tracing); note the boundary explicitly.
- **threat:E5** 8 scenarios, one attack ontology
  - next: Add multi-hop / delayed-instruction families (see DATASET_AUDIT)

### internal
- **threat:I1** Parser converts format non-compliance into a fake safety finding
  - next: Parser fuzzing over recorded real replies; assert no silent Finish on well-formed tool JSON.
- **threat:I3** Detector logic bug inflates precision/recall
  - next: Mutation testing on detectors; adversarial label review
- **threat:I4** non_completion fires on legitimately long tasks
  - next: Add a multi-step-completion scenario; confirm the detector's scope is documented, not assumed.
- **threat:I5** Determinism assumption is false for LLM subjects
  - next: Byte-diff all six across two runs; record any drift as a caveat

### statistical
- **threat:S1** n=8 scenarios cannot support ordinal rankings
  - next: Keep the scope sentence load-bearing; no per-scenario CI (would be theater).
- **threat:S2** Detector P/R rests on 68 single-annotator items
  - next: Inter-rater kappa on a ~20-item subset (blocked on a second annotator).
- **threat:S3** Class imbalance in the corpus
  - next: Report macro alongside micro (cheap; add at next validate touch)
- **threat:S4** Selection bias in the sampled-real cohort
  - next: Grow the sampled-real cohort each benchmark cycle

## Contract findings

All contracts hold.

## Labeling needs

- **threat:S2** annotators: 1, kappa: blocked_on_second_annotator

No aggregate verdict: assurance is reported per conclusion, not per repository.
