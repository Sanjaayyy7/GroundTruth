# Judge Rerun — Results

**Pre-registration:** `docs/specs/2026-08-02-judge-rerun-preregistration.md` @ `3d00783`
(the `predictions_commit`; D10 verifies ancestry mechanically).
**Protocol:** 68-item labeled corpus, temperature 0, seed 42, same Validation Engine as the rules.
**Raw evidence:** `runs/experiments/judge-rerun-2026-08-02/` — per-cell metrics, raw replies,
parse-failure counts, and the P1 gate record.

## The question

Is the published rules-versus-judge gap substantially an artifact of this harness?

C7 reported `llama3.1:8b` at precision 0.2254 with 110 false positives, measured while `chat()`
forced `format=json` for every caller and the judge prompt asked for a JSON *array*. A second
confound was found while repairing threat I1 and fixed before any arm ran: the judge's own parser
searched for a lazy `[...]` before considering any object, so a constrained reply carrying a bracket
inside a string value returned no categories and failed open as recall loss.

## All eight cells

| Arm | Decode | Prompt | Parser | Subject | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|---|---|---|---|
| A0 | json | array | legacy | llama3.1:8b | 0.2254 | 0.6809 | 0.3387 | 32/110/15 |
| A0 | json | array | legacy | gemma3:4b | 0.3137 | 0.3404 | 0.3265 | 16/35/31 |
| A1 | json | array | current | llama3.1:8b | 0.2353 | 0.6809 | 0.3497 | 32/104/15 |
| A1 | json | array | current | gemma3:4b | 0.3137 | 0.3404 | 0.3265 | 16/35/31 |
| **B** | **json** | **object** | current | **llama3.1:8b** | **0.3600** | 0.5745 | **0.4426** | 27/48/20 |
| **B** | **json** | **object** | current | **gemma3:4b** | **0.3571** | 0.5319 | **0.4273** | 25/45/22 |
| C | none | array | current | llama3.1:8b | 0.1824 | 0.6170 | 0.2816 | 29/130/18 |
| C | none | array | current | gemma3:4b | 0.2857 | 0.6809 | 0.4025 | 32/80/15 |

Rules, for comparison, on the same corpus through the same engine: **P 0.9545 · R 0.8936 · F1 0.9230**.

## `llama3.1:8b` false positives by category

| Arm | total | instruction_hijacking | unsafe_tool_invocation | secret_exfiltration | goal_drift | over_refusal |
|---|---|---|---|---|---|---|
| A0 | 110 | 53 | 23 | 16 | 18 | 0 |
| A1 | 104 | 50 | 20 | 16 | 18 | 0 |
| **B** | **48** | **17** | 11 | 6 | 10 | 4 |
| C | 130 | 55 | 49 | 23 | 3 | 0 |

Aligning the decode constraint with the prompt shape cuts hijacking false positives from 53 to 17,
a 68% reduction, and total false positives by 56%.

## Predictions

| | Prediction | Verdict |
|---|---|---|
| **P1** | A0 reproduces published precision within ±0.03 | **CONFIRMED** |
| **P2** | The parser fix changes total detections by <10% | **CONFIRMED** |
| **P3** | Arm B raises `llama3.1` precision by ≥0.10 absolute over A1 | **CONFIRMED** |
| **P4** | Arm C raises precision for both subjects, lowers recall for at least one | **FALSIFIED** |
| **P5** | Rules precision exceeds the best judge arm for both subjects | **CONFIRMED** |

**P1.** `llama3.1:8b` reproduced the published figure exactly — 0.2254 against 0.2254, delta
0.0000, id-for-id on the false-positive list. `gemma3:4b` measured 0.3137 against a published
0.3387, delta −0.0250, inside the pre-registered tolerance. ADR-0003 already refuses to claim local
inference is bit-deterministic; this is what that refusal looks like when it is measured.

**P2.** Detections (tp+fp) moved 142 → 136 for `llama3.1:8b`, 4.2%, and were unchanged for
`gemma3:4b`. The parser defect was real and had been live for five milestones, but under a decode
constraint it rarely bit. It is not the explanation for C7.

**P3.** 0.2353 → 0.3600, +0.1247 absolute, +53% relative. **The confound was real and it was large.**

**P4 — falsified, and this is the useful result.** The prediction was that removing the decode
constraint would trade recall for precision. Precision *fell* for both subjects — `llama3.1:8b`
0.2353 → 0.1824, `gemma3:4b` 0.3137 → 0.2857 — and `gemma3:4b`'s recall doubled rather than
dropping. Parse failures were **0 of 68** in both unconstrained cells, so the fail-open mechanism
never fired and cannot explain it; the judges simply flagged far more categories when nothing
constrained the shape of their answer.

The reasoning behind P4 was that the constraint was the problem. It was not. **The mismatch was the
problem.** An unconstrained judge is worse than a judge constrained in the wrong shape, and both are
worse than a judge whose constraint and prompt agree. That is a sharper claim than the one
pre-registered, and it was only available because the arm that could refute the guess was run.

**P5.** Rules at 0.9545 exceed the best judge arm (0.3600) by a wide margin for both subjects. This
was the prediction most worth losing and it held.

## What this changes

C7's headline survives: rules beat local LLM judges on this corpus by a large margin, and the
ordering is not an artifact. But C7's *scope* was wrong, and the number attached to it was measured
under a confound the claim never disclosed. The honest reading is that **0.2254 understated the
judge by about 60%** — the defensible figure for a local 8B judge on this corpus, prompted and
constrained consistently, is 0.36.

The methodological finding stands on its own and generalizes past this repository: **an LLM-judge
evaluation is sensitive to agreement between the decode constraint and the prompt's requested shape,
and a mismatch cost 0.135 precision here.** Anyone comparing judges without pinning both is
measuring their harness.

## Limits

- Two subjects, both small local models. Nothing here transfers to frontier judges; **threat E1
  stays open and undischarged**, and no arm should be read as addressing it.
- The corpus is the one the rules were developed against, so rules keep home-field advantage in
  every arm. This experiment tested the harness, not the contamination (threat A2, debt #19).
- n = 68, one annotator. No arm supports a ranking claim, and none is made.
- Arm A0's legacy parser exists only to reproduce a historical number. It is not reachable from the
  CLI and is not a supported option.
