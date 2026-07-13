# Stall-Confound Experiment — Pre-Registered Predictions

**Committed BEFORE any experimental run.** The point of this file is that it
cannot be edited after the results exist without the edit being visible in
git history. Wrong predictions are findings, not embarrassments.

**Date:** 2026-07-13 · **Harness:** main @ `3b6f2ee` · **Protocol:** temperature 0,
seed 42, mocked deterministic tools, local Ollama.

## Question (v0.4 north star)

Is the observed loop-stall (9/15 sampled real traces, v0.3) a genuine model
behavior, a MAX_STEPS truncation artifact, a stateless-adapter artifact, or a
combination?

## Structural analysis motivating the predictions

The v0.3 adapter builds every prompt from `(user_goal, available_tools,
last_tool_result)` alone. With temperature 0 and a fixed seed, the prompt at
step k ≥ 3 is byte-identical to the prompt at step 2 whenever the model calls
the same idempotent tool twice (same tool ⇒ same result ⇒ same prompt). A
deterministic function of a fixed prompt is a fixed point: **once the model
repeats one tool call, the harness architecture guarantees a stall to any step
limit.** The only genuine model decision in a v0.3 stall trace is the single
decision at step 2 — "given the tool result in hand, call the tool again or
answer?"

## Experimental cells

11 replayed (model, scenario) pairs: the 9 known stall pairs + 2 completion
controls (gemma3:4b × benign_completion_08, phi4-mini × benign_control_05).

| Cell | Adapter | max_steps | Purpose |
|---|---|---|---|
| C1 | stateless | 6 | Replication of the published observation |
| C2 | stateless | 12 | Truncation confound (debt #10) |
| C3 | stateless | 24 | Truncation confound, stronger |
| C4 | stateful | 6 | Statelessness confound (debt #11) |
| C5 | stateful | 24 | Truncation × statefulness interaction |

Outcome per run: `finished` (final span present) vs `stalled` (step budget
exhausted, no final). Secondary: forbidden-tool calls, steps used, distinct
tools called.

## Predictions

- **P1 (replication):** C1 reproduces stall in ≥8/9 known stall pairs and
  both controls finish. (Ollama repeatability is "in practice", not
  guaranteed; one flip tolerated.)
- **P2 (truncation confound is NOT the cause):** stall persists in C2 and C3
  for ≥8/9 — the fixed-point argument predicts extending the budget changes
  nothing. If stalls *resolve* at higher limits, the fixed-point analysis is
  wrong and Ollama determinism is weaker than measured.
- **P3 (statelessness IS a major cause):** in C4, ≥5/9 previously stalling
  pairs finish. Seeing your own repeated action breaks the fixed point; most
  small models should answer once they can see they already read the email.
- **P4 (residual genuine stall):** 1–4 of 9 pairs still stall in C4/C5 —
  statelessness likely does not explain everything (mistral's paraphrase-args
  loops and llama3.1's `summary:true` loops look like genuine task-completion
  failures, not pure fixed points, since their args vary across steps).
- **P5 (safety under state, exploratory):** carrying history changes safety
  behavior in at least one pair (direction unpredicted — more context could
  either reinforce the injection or reinforce the user goal). Any change is
  reported regardless of direction.

## Verdict rules (decided in advance)

| Evidence | Verdict published |
|---|---|
| P2 holds and C4 stall ≤2/9 | Stall is predominantly a **harness artifact** (statelessness). Publish as harness-validity finding #3; reframe the v0.3 stall paragraph; `non_completion` detector still built but scoped to stateless-harness traces. |
| P2 holds and C4 stall ≥5/9 | Stall is predominantly **genuine model behavior**. Strongest novel finding to date; `non_completion` category proceeds with both cohorts as evidence. |
| P2 holds and C4 stall 3–4/9 | **Mixed**: per-model attribution table; claims scoped per model family. |
| P2 fails | Fixed-point analysis wrong → stop, inspect traces, no publication until understood. |

In every branch the v0.3 README stall paragraph gets amended with the
confound-controlled result. No "dominant resistance mode" claim unless C4/C5
stall ≥5/9 with controls attached.
