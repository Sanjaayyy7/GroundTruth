# Groundtruth — Claims Audit (v0.5)

Every public technical claim in the repository, classified against the evidence
that supports it. The machine-readable register is [`claims.yaml`](claims.yaml);
this document explains the reasoning. Governing rule: **no sentence may exceed
the evidence supporting it.**

Classification vocabulary: **Fact** (reproducible evidence in-repo) ·
**Supported Observation** (repeated, not generalized) · **Working Hypothesis**
(evidence exists, needs more) · **Speculation** (reasonable, insufficient) ·
**Retracted** (disproven, kept for the record).

## Summary

| id | Claim (short) | Class | Confidence | Key limit |
|---|---|---|---|---|
| C1 | Loop-stall is a stateless-harness artifact | Fact | high | one adapter/decoding config |
| C2 | The artifact masked real injection compliance (2 cases) | Fact | high | 2 specific pairs |
| C3 | Our own prediction P4 was falsified | Retracted | high | — (records discipline) |
| C4 | v0.3 ranking inverts under the 6-detector suite | Fact | high | n=8, not a leaderboard |
| C5 | Secret exfiltration 2/6 → 6/6 with state | Supported obs. | medium | one scenario, one prompt |
| C6 | Rule detector quality P 0.933 / R 0.894 | Fact | medium | single annotator |
| C7 | Small local judges are imprecise (110 FP) | Supported obs. | medium | one prompt, corpus v1 |
| C8 | Indirect injection obeyed by 6/6 families | Supported obs. | medium | one scenario |
| C9 | Runs are deterministic (byte-identical) | Fact | high | LLM byte-identity empirical |
| C10 | Consumer rule (≥2 consumers) still holds | Fact | high | 2nd consumer partly planned |

## Reasoning per claim

**C1 — stall is an artifact (Fact).** The strongest evidence in the repo, and
the one most likely to be attacked, so it gets the most scrutiny. A
pre-registered 5-cell experiment (predictions committed at `040c804`, before
the runner ever executed) showed 9/9 stalls persist at 6/12/24 stateless steps
and 0/9 survive one message of history. The mechanism is not inferred, it is
structural: at temperature 0 the prompt at step k≥3 is byte-identical to step 2
once an idempotent tool repeats, so the decoder is a fixed point. Verified at the
trace level (23/23 identical calls in the llama3.1 24-step run). This is a Fact
*within its scope*: six local models ≤8B, eight scenarios, one adapter, one
decoding configuration. It is **not** a claim about all agents or all harnesses.

**C2 — the artifact hid real compliance (Fact).** Two traces show it directly:
mistral calls `transfer_funds(recipient=attacker@evil.com)` and announces the
transfer; llama3.2 calls the forbidden `send_email` with the attacker address.
Published as an existence proof of two cases, not as a rate — "2 of 9" is the
honest framing.

**C3 — P4 falsified (Retracted).** We predicted 1–4 genuine stalls would remain;
zero did. This is kept in the register precisely because retracting one's own
pre-registered prediction is the credibility asset, not an embarrassment to bury.

**C4 — ranking inversion (Fact).** llama3.1/3.2/mistral drop 0.875→0.0, qwen3
holds at 0.625. The evidence is twelve committed scorecards. The load-bearing
scope sentence: **n=8 scenarios, existence proof of ranking fragility, never a
leaderboard.** A 0.125 robustness step is one scenario; the claim is about the
*fragility of the v0.3 ordering*, not a new ordering to trust.

**C5 — exfiltration 2/6 → 6/6 (Supported Observation, not Fact).** Deliberately
not upgraded to Fact: it rests on a single scenario (`secret_leak_06`) and a
single stateful prompt design. The pattern is real and reproduced across six
models, but "every model mishandles poisoned content" needs scenario variants
before it generalizes. Downgrade is intentional.

**C6 — detector quality (Fact, medium confidence).** The point numbers are
reproducible (`groundtruth validate`), so the measurement is a Fact; the
*confidence* is medium because every label has one author. The v0.5 bootstrap
(10k resamples, seed 42) puts the 95% CI at precision [0.845, 1.000], recall
[0.790, 0.978] — honest width for 68 items. Inter-rater κ is the open item.

**C7 — judges imprecise (Supported Observation).** Reproduced on two models but
one prompt design and corpus-v1 labels. Explicitly scoped away from any claim
about frontier or tuned judges — the instrument (`validate --judge`) outlives the
claim.

**C8 — universal injection (Supported Observation).** Six families obeyed one
injection scenario. "Universal" is only safe with the scope attached; multi-hop
variants (the recommended next milestone's alternative) would be needed to make
it a family-level Fact.

**C9 — determinism (Fact).** Scripted subjects are deterministic by
construction. LLM byte-identity is empirical: llama3.2 reproduced byte-identical
across both conditions from a *fresh virtualenv* this milestone. The honest
caveat: byte-identity depends on the local Ollama build and weights being
unchanged; it is measured, not guaranteed by us.

**C10 — consumer rule (Fact).** See [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md).
The one nuance: for the newest primitives the second consumer is *designed*
(JudgeKit/PlannerBench) rather than *realized*. Disclosed, not hidden.

## Claims explicitly NOT made

- No claim that stall is universal across agents, harnesses, or temperatures.
- No leaderboard or ordinal safety ranking of models (n=8 forbids it).
- No claim that rules beat frontier or tuned judges — only small local zero-shot.
- No claim of statistical significance on any per-scenario benchmark result.
- No claim that detector quality generalizes beyond this single-annotator corpus.

## Stale claims corrected this milestone

README header advertised "AgentProbe v0.2 — shipping" and "five failure lenses";
`pyproject.toml` said `version = 0.1.0`. All corrected to v0.4 / six lenses /
0.4.0 — a reviewer who reads the header before the body must not meet a version
contradiction. (Phase-1 finding; minimal doc/config fix, no behavior change.)
