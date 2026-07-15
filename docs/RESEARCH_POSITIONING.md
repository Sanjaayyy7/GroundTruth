# Groundtruth — Research Positioning (v0.5)

An objective account of what is genuinely novel, what is competent engineering,
and what is existing practice. Every conclusion is tied to repository evidence.
No marketing.

## What is genuinely novel

1. **Measuring the measurement instrument, then catching it lying — three
   times, on the record.** Two parser incidents (agent, judge) and one
   controlled confound experiment (stall). The third is the strongest: a
   *pre-registered* experiment that falsified the project's own headline
   hypothesis and found real injection compliance the harness had been hiding.
   Evidence: `experiments/stall_confounds/`, `CLAIMS.md` C1–C3. **No evaluation
   framework surveyed publishes the precision/recall of its own scoring machinery
   or pre-registers experiments against its own findings.** This is the one
   genuinely novel contribution.

2. **Non-completion as a first-class trace outcome, with its cause attributed.**
   The taxonomy expresses "safe but never answered," and the confound experiment
   attributes it to stateless observation rather than model behavior. The
   surveyed ecosystem treats budget exhaustion as either a pass (robustness) or
   silence. Evidence: `NonCompletion` detector, C4.

## What is competent engineering (not novel, done well)

- Deterministic offline harness with mocked tools ($0, byte-reproducible).
- Explanatory `Failure` objects (category/severity/causal-chain/fix) instead of
  scores. A strong design choice; not a research result.
- A self-CI regression gate, schema versioning, static HTML report. Standard
  engineering, executed cleanly.

## What is existing practice

- Prompt-injection / tool-misuse scenarios — a known and active area
  (Inspect AI, agent red-team literature). Groundtruth's scenarios are a small,
  honest sample, not a novel attack taxonomy.
- LLM-as-judge — well-established; Groundtruth's contribution is *measuring* a
  judge against labeled traces, not the judge idea itself.
- Bootstrap CIs, threats-to-validity structure — standard scientific method,
  applied here (which is itself the point, but not novel).

## Differentiation (evidence-backed)

Against the ecosystem (full table in POSITIONING.md), the single conceptual gap
Groundtruth occupies: **it self-measures and self-falsifies.** LangSmith/Phoenix
observe production; DeepEval/Promptfoo count metrics they never validate;
Inspect AI is rigorous but unopinionated and does not measure its own detectors.
The differentiator is a *methodology and a track record*, not a feature — which
is also why the moat is data + norms, not code (STRATEGY.md §7).

## What should NOT be claimed

- Not "a benchmark of model safety" — n=8, existence proofs only.
- Not "rules beat LLM judges" unqualified — only small local zero-shot judges,
  one prompt, corpus-v1 labels.
- Not "universal injection" without scope — one scenario, six ≤8B models.
- Not any generalization to frontier models — none tested.
- Not statistical significance on per-scenario results.

## Interview-safe vs replication-required

| Finding | Interview-safe now | Needs replication first |
|---|---|---|
| Stall is a harness artifact (C1) | ✅ with scope | — |
| Pre-registered, then falsified own P4 (C3) | ✅ (this is the story) | — |
| Ranking inverts once stalls are visible (C4) | ✅ as fragility, not leaderboard | — |
| Harness-validity incidents ×3 (methodology) | ✅ | — |
| Detector quality P/R (C6) | ✅ with "single annotator" | κ for a stronger claim |
| Exfiltration 2/6→6/6 (C5) | ⚠️ as one-scenario observation | scenario variants |
| Universal injection (C8) | ⚠️ with scope | multi-hop variants |

## How a skeptic would describe this project

**Skeptical Staff Engineer:** "Small deterministic eval harness, ~545 LOC core,
78 tests, clean consumer-rule architecture. The impressive part isn't the code —
it's that they caught their own instrument lying three times and published it,
including a pre-registered experiment that killed their own headline claim. That
is the exact trait I screen for: distrust of your own green checkmark."

**Skeptical Researcher:** "Not a paper — n=8 scenarios, single-annotator labels,
≤8B local models, no frontier baseline. But the *method* is sound: pre-registered
predictions, falsification, threats-to-validity, reproducible byte-identical
runs. It's an honest technical note (arXiv + blog), not a NeurIPS submission, and
it correctly says so. The stall-artifact-masking-compliance result is a real,
citable methodology contribution."

Both descriptions are things to be proud of, and both are already true from the
repository evidence — which is the point of v0.5.

## v0.6 positioning candidates (evidence-mapped, headline gated)

v0.6 shipped the meta-evaluation engine: `groundtruth audit` constructs an
evidence graph from the registers and derives a quality manifest + assurance
report, with contracts CT1–CT10 failing CI on drift. That changes what the
project can honestly call itself. Candidates, mapped to artifacts:

| Candidate | Supporting artifacts | Gaps |
|---|---|---|
| Evaluation Framework | core/ + products/agentprobe/ + 116 tests; CLI run/validate/ci/report | undersells: says nothing about the self-validation apparatus |
| Evaluation Validation Platform | detector-quality corpus + measured misses + CT5 metric provenance | "platform" implies breadth; one product line exists |
| **Evaluation Assurance Platform** | assurance report (per-conclusion justification), contracts, manifest, claims/threats registers, ADR-0006 | "platform" still ahead of one realized consumer; strongest fit for what v0.6 actually built |
| Evaluation Reliability System | determinism (C9) + repro guide + CI gates | "reliability" reads as uptime engineering; misses the epistemic layer |
| Evaluation Infrastructure | register formats (claims v2, threats v1) designed for future consumers | requires a second consumer (JudgeKit) that does not exist yet |

**Best-supported today:** *Evaluation Assurance Platform* — with the honest
caveat that "platform" is earned only after JudgeKit consumes the same
registers. Until then, the defensible one-liner is: **"an agent-evaluation
framework that audits its own evidence."** Every noun in that sentence has a
committed artifact behind it.

### v0.7 update

External validation moved the "Evaluation Infrastructure" gap from *no
second consumer* to *no independently authored consumer*: MiniJudge
(claim C11, pre-registered) proves the register formats and the unmodified
engine carry a second evaluation, but it shares author and repository with
Groundtruth (threat E6). The defensible one-liner is now: **"an
agent-evaluation framework that audits its own evidence — and has
demonstrated that audit on a second evaluation's registers."** The
"Evaluation Assurance Platform" headline remains gated on an externally
authored consumer (E6's discharge experiment), per ADR-0007.

The README headline is deliberately unchanged: the repository earns its
identity from artifacts, and the framing decision is gated on the owner's
review, not on this document.
