# Judge Rerun — Pre-registered Protocol

**Committed before any arm is run.** This commit's SHA is the
`predictions_commit` for the resulting claim; the commit carrying the results
artifacts will be the `results_commit`, and D10 will verify ancestry
mechanically, as it did for the stall experiment.

## The single scientific question

Is the published rules-versus-judge gap substantially an artifact of this
harness rather than a property of LLM judges?

C7 reports rules at precision 0.9143 against `llama3.1:8b` at 0.2254 with 110
false positives, 53 of them `instruction_hijacking`. The claim's scope says
"one prompt design." It does not say "under a JSON-object decode constraint
that contradicts the prompt," which is what actually ran.

This is the third time this project has asked whether its own instrument
manufactured a result. The first two answers were yes.

## The two confounds under test

**Confound 1 — decode constraint fights the prompt.** `chat()` hardcodes
`"format": "json"` for every caller. Ollama's `format=json` biases decoding
toward an object. The judge system prompt asks for *"ONLY a JSON array of the
categories."* The symptom was observed at v0.3 — the first comparison returned
zero recall for both judges because they emitted `{"category": bool}` — and the
**parser was patched instead of the conflict being removed**. The 110 false
positives have never been measured with the conflict absent.

**Confound 2 — the judge's own parser discarded verdicts.** Found while
repairing threat I1 in the agent adapter, and not previously recorded. The
judge parser searched for a lazy `[.*?]` *before* considering any object, so a
constrained object reply carrying a bracket inside any string value matched the
prose bracket, failed to parse, and returned no categories at all. The judge
then failed open, and the detection vanished as recall loss. Fixed in
`2263f9c`, before this protocol was written and before any arm is run.

Threat I1 was recorded against the agent adapter at v0.3 and never checked for
elsewhere. It was live in the judge for five milestones. That is a finding
about the register, not only about the parser: **a recorded threat was treated
as discharged for the one call site where it was found.**

## Design

Two subjects x four arms, on the same 68-item labeled corpus, through the same
Validation Engine, with the same seed and temperature.

| Arm | Decode constraint | Prompt shape | Parser | Purpose |
|---|---|---|---|---|
| **A0** | `format=json` | array | pre-`2263f9c` | instrument faithfulness — reproduce the published number |
| **A1** | `format=json` | array | current | isolates confound 2 |
| **B** | `format=json` | object | current | constraint and prompt agree |
| **C** | unconstrained | array | current | prompt as designed |

Subjects: `llama3.1:8b`, `gemma3:4b`. Frontier judges are **out of scope** —
no API access. Threat E1 stays undischarged and must not be reported otherwise.

A0 exists because an instrument is not trusted until it reproduces a known
result. The re-scoring path added in this same milestone was gated the same
way, and the stall experiment's byte-level verification served the same role.
If A0 fails to reproduce, every other arm is uninterpretable and the experiment
stops there.

## Predictions

Locked before execution. Stated so that each can be shown false.

- **P1 — faithfulness.** A0 reproduces published precision within ±0.03 for
  both subjects: `llama3.1:8b` 0.2254, `gemma3:4b` 0.3387. ADR-0003 already
  refuses to claim local inference is bit-deterministic, so the tolerance is
  stated rather than assumed to be zero.
- **P2 — the parser effect is small.** A1 changes total detections by less than
  10% against A0 for both subjects. The defect only bites when a string value
  contains a bracket, which should be uncommon under a decode constraint.
- **P3 — alignment is the dominant confound.** Arm B raises `llama3.1:8b`
  precision by at least 0.10 absolute over A1. Mechanism: forced into object
  mode while asked for an array, the model resolves the conflict by emitting a
  flag object with most fields true, which is exactly the observed 110-FP
  signature.
- **P4 — unconstrained decoding trades recall for precision.** Arm C raises
  precision over A1 for both subjects and lowers recall for at least one,
  because an unparseable reply fails open and a fail-open is a missed
  detection.
- **P5 — rules still win on precision.** Rules precision exceeds the best judge
  arm for both subjects.

P5 is the prediction most worth losing. If a judge arm beats the rules once the
harness stops fighting it, that is a larger and more interesting result than the
one currently published, and it will be reported as the headline.

## What gets published, in every branch

- If precision moves materially: a new finding about decode-constraint
  sensitivity in LLM-judge evaluation, and C7 is amended with its scope
  corrected. A measured claim that "a mismatch between decode constraint and
  prompt shape cost 0.68 precision" is a statement about eval methodology, not
  about this repository.
- If precision does not move: C7 is strengthened, because the obvious confound
  is now excluded by experiment rather than by argument.
- If P1 fails: the experiment is reported as inconclusive and no arm is quoted.

No arm is dropped after the fact. All four are reported for both subjects
including any that are unflattering, and the raw per-arm reports are committed
as artifacts.

## Declared exploratory, not pre-registered

A hybrid detector — rules as a high-precision first pass, judge invoked only on
rule-negative traces — will be measured on the same corpus with the same
machinery. It is an engineering addition rather than a hypothesis under test,
carries no prediction here, and will be labelled exploratory wherever it is
reported. Law 12 permits one hypothesis per milestone and this protocol spends
it on the confound question.

## Threats to this protocol

- **Same author, same corpus.** The corpus is the one whose labels the rules
  were developed against, so the rules keep home-field advantage in every arm.
  This experiment tests the harness, not the contamination (threat A2, debt
  #19, open since v0.3).
- **n = 68, one annotator.** No arm produces a ranking claim. Differences are
  reported as measured differences with the corpus size in the same sentence.
- **Two subjects, both small local models.** Nothing here generalizes to
  frontier judges. E1 remains open and is not addressed by this work.
- **Arm A0 requires restoring retired parser behaviour** behind a flag. That
  code path exists only to reproduce a historical number and must not become a
  supported option.
