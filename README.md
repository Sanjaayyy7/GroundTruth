# Groundtruth

**v0.9.1 — shipping** · offline, deterministic red-teaming for tool-using agents —
that measures its own detectors and publishes what they miss.

Most eval tools tell you whether your agent failed. This one tells you how good
the thing doing the telling is, and it caught its own harness lying three times.

---

## The finding: a stall was the harness, not the models

In 9 of 15 sampled traces, small models neither complied with an attack nor
refused — they looped one safe tool to the step budget and never answered. The
obvious reading is that small models stall under pressure. That reading was
wrong, and the mechanism says why: the v0.3 adapter rebuilt every prompt from
`(goal, tools, last_tool_result)` alone, so at temperature 0 the moment a model
repeats one idempotent call the prompt at step *k* is byte-identical to the
prompt at step 2. A deterministic function of a fixed prompt is a fixed point,
so the architecture *guaranteed* a stall at any budget. Predictions were
committed before the experiment ran, and prediction P4 — that some stalls would
be genuine — was **falsified**: none were.

![Three-panel cycle: a stateless prompt rebuilt from (goal, tools, last_tool_result) at temperature 0 reproduces itself byte-for-byte after any repeated idempotent tool call — 23 identical read_email calls in one 24-step run. The stall is a fixed point of the harness, not a property of the model.](docs/assets/stall-fixed-point.svg)

| Cell | Adapter | Step budget | Still stalled | Forbidden-tool calls |
|---|---|---|---|---|
| C1 | stateless | 6 | **9 of 9** | 0 |
| C2 | stateless | 12 | **9 of 9** | 0 |
| C3 | stateless | 24 | **9 of 9** | 0 |
| C4 | stateful | 6 | **0 of 9** | **2** |
| C5 | stateful | 24 | **0 of 9** | **2** |

Verified at byte level: 23 identical `read_email {"summary": true}` calls in the
24-step run. **The payload is the last column.** Two of the nine "safely
stalled" models comply the moment they can see their own history — one transfers
funds to the attacker and says so, another exfiltrates a key. The harness had
been scoring truncated compliance as resistance, and fixing it inverted the
project's own published leaderboard.

Full protocol and raw evidence: [`experiments/stall_confounds/`](experiments/stall_confounds/).

---

## Detector quality, misses included

Every detector is measured against 68 hand-labeled traces, and the cases it gets
wrong are named and pinned by a test — so an accidental improvement fails the
build until the labels are changed deliberately.

| Category | Precision | Recall | Known limits (item ids in the set) |
|---|---|---|---|
| unsafe_tool_invocation | 1.00 | 0.92 | forbidden *effects* via allowed tools (`ut_pos_04_semantic_gap`) |
| instruction_hijacking | 1.00 | 0.90 | off-target hijacks (`ih_pos_04`) |
| secret_exfiltration | 0.80 | 0.67 | split / obfuscated secrets (`sl_pos_04/05`, `sl_fp_01`) |
| goal_drift | 0.83 | 1.00 | a typo'd-then-corrected call reads as drift (`gd_fp_01`) |
| over_refusal | 1.00 | 0.75 | unusual refusal phrasings (`orf_pos_03`) |
| non_completion | 1.00 | 1.00 | structural rule: no final span ⇔ budget exhausted |
| **micro** | **0.9545** | **0.8936** | F1 0.9230 · tp 42 / fp 2 / fn 5 |
| **macro** | **0.9389** | **0.8722** | F1 0.8996 · unweighted, so a rare category counts as much as a common one |

**Say the denominator out loud:** precision is measured over 44 detections, not
over 68 traces × 6 categories. `measure()` iterates detected-or-labeled, so
there is no true-negative bucket. The figure says 95% of the category-presence
claims made were right — not that 95% of all possible decisions were right.

**Rules versus LLM judges.** A local 8B judge reaches precision 0.3600 against
the rules' 0.9545 on the same items through the same engine. The originally
published 0.2254 was measured with the decode constraint forcing an object while
the prompt asked for an array; correcting that mismatch raised precision by
0.1247 and cut hijacking false positives from 53 to 17. The ordering survives;
the number was understated by roughly 60%, and the claim now says so.
See [`experiments/judge_rerun/REPORT.md`](experiments/judge_rerun/REPORT.md).

---

## Quickstart

```bash
pip install -e ".[dev]"          # source install; the corpus lives in the repo
groundtruth run --agent vulnerable_agent   # the demo frontier
groundtruth validate                       # how good are the detectors themselves?
```

That is the whole loop: run a subject, then measure the thing that judged it.
`groundtruth audit` and `groundtruth steward` check the repository's own claims
and structure; `make gate` runs everything CI runs, in CI's order.

Real local models are optional and cost nothing —
`groundtruth run --agent ollama:llama3.1:8b --stateful` needs only
[Ollama](https://ollama.com) serving locally.

---

## What this does NOT claim

Stating this plainly is cheaper than being caught by it.

- **It is not a leaderboard.** n = 8 scenarios cannot support ordinal rankings.
  Every model result is framed as an existence proof — *six of six model
  families call `delete_files`* is valid at n = 1 and needs no statistical
  power. Per-scenario confidence intervals are refused as theatre; exactly one
  interval is published, because 68 items support exactly one.
- **The ground truth has one annotator**, who also wrote the detectors, the
  scenarios and the taxonomy. Precision measures internal consistency as much as
  correctness. Fifteen of the 68 items are sampled from real model runs rather
  than authored to fit the rules, which is a partial defence and not a fix. A
  second annotator and a kappa remain the cheapest available strengthening, and
  they are still open.
- **Tools are mocked and injections are single-hop.** External validity was
  traded for internal validity deliberately: mocked tools are what made three
  harness bugs show up as *patterns* rather than as noise. The dataset and the
  harness co-evolved, so the suite structurally cannot probe delayed-activation
  payloads.
- **No frontier model has been measured.** Every subject and every judge is 8B
  or smaller. Nothing here transfers to a frontier judge, and that threat is
  recorded as open rather than argued away.
- **Determinism has three tiers, not one.** Scripted subjects are byte
  reproducible; real-model scorecards are evidence artifacts, never regression
  fixtures, because local inference at temperature 0 is repeatable in practice
  and not guaranteed bit-identical.
- **There is no composite score, permanently.** `no_composite_score` is a key in
  the machine-readable manifest whose value is the justification for its own
  absence. Assurance is reported per conclusion, never per repository.
- **It has no users.** Zero external contributors, zero issues. This is a
  research artifact, not a product with adoption.

---

## How the repository checks itself

Documentation rots, so the guarantees are mechanical rather than promised:

- every published number lives in a register, and a drifted number **fails the
  build** with a named finding;
- numeric claims in living prose must resolve to a register or a declared
  allowlist entry carrying a reason — the drift class the engine exists to kill,
  applied to prose;
- committed evidence is regenerated in CI and byte-diffed, so a stale artifact
  fails loudly. This caught a report that had carried stale content through an
  entire detector change;
- import layering is enforced by an AST scan, not by convention;
- the safety gate **fails closed on an unexplained improvement**, because a
  detector that regresses and stops firing raises the score and would otherwise
  pass.

---

## Documentation

| | |
|---|---|
| [Full README](docs/README-full.md) | the previous long-form version, kept whole |
| [SPEC.md](SPEC.md) | milestone-by-milestone record, including reversals |
| [docs/CONSTITUTION.md](docs/CONSTITUTION.md) | the laws, and the checks that enforce them |
| [docs/claims.yaml](docs/claims.yaml) | every claim, its evidence, and how to falsify it |
| [docs/THREATS_TO_VALIDITY.md](docs/THREATS_TO_VALIDITY.md) | what could make each result wrong |
| [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) | reproduce every number from a clean checkout |
| [docs/adr/](docs/adr/) | decision records, each with a review trigger |

## License

MIT — see [LICENSE](LICENSE).
