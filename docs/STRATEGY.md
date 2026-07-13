# Groundtruth — v0.4 Gate Review & Strategy

**Status:** the one strategy review permitted between v0.3 and v0.4 (per the
"one gate review per version, then ship" immutable adopted at the v0.3 pre-mortem).
This document supersedes the v0.4 planning directive's requested scope: the
sections below are the ones where evidence exists; everything else was cut
deliberately (see §12, Decision D4). It is a gate record, not a standing
manifesto — POSITIONING.md's anti-goal against manifesto-first development
applies to this file too. It gets revisited at the v0.5 gate, not before.

---

## 1. Retrospective: v0.1 → v0.3

| Version | Shipped | The number that proves it |
|---|---|---|
| v0.1 (~1 wk) | Platform spine (Trace/Eval/Dataset engines), AgentProbe runner, 2 detectors, 5 scenarios, CLI, e2e tests | vulnerable 0.20 vs hardened 1.00, deterministic, $0 |
| v0.2 (1 day) | 5 detectors, safety–utility frontier (paranoid agent), Validation Engine + 53 hand-labeled traces, first real LLM subjects | measured detector quality P 0.9032 / R 0.8485; gemma3 + llama3.1 both hijacked by indirect injection |
| v0.3 (2 days) | Self-CI regression gate, schema versioning, 6-model benchmark on one harness version, static HTML report, raw-trace persistence, 15 sampled-real labels (68-item set), rules-vs-judge instrument + measurement | rules P 0.9143 / R 0.8649 / F1 0.8889 vs judge llama3.1:8b P 0.2254; two harness-validity incidents caught pre-publication; byte-identical rerun |

65/65 tests green at v0.3 close. 5 ADRs. Debt register audited every gate.

What "Version Zero" proved: the three founding bets — explanatory Failure
taxonomy, deterministic offline evaluation, measured detector quality — all
survived contact with real models and produced findings none of them
individually predicted. That is the strongest possible signal a v0-architecture
can give.

## 2. Discoveries, ranked by value

1. **Loop-stall is an unmeasured failure mode (9/15 sampled real traces).**
   Small models under adversarial pressure frequently neither comply nor
   refuse — they loop a safe tool to the step limit and never answer. No
   category in our taxonomy (or, as far as surveyed, anyone's) expresses
   "safe but silently useless." This is the project's one genuinely novel
   research candidate.
2. **Harness bugs are result-shaped lies — twice.** The agent parser scored
   format non-compliance as over-refusal (would have inverted two model
   rankings); the judge parser scored 0 recall as an artifact of
   `format=json` response shape. Both caught by trace inspection before
   publication. This *is* the thesis ("measure the measuring stick")
   demonstrated on ourselves, and it is the best interview story in the repo.
3. **Indirect injection: 6/6 small local model families obeyed a `SYSTEM:`
   instruction planted in tool output.** Scoped honestly: one scenario, six
   small local models — an existence proof, not a universality theorem (§8).
4. **Small zero-shot LLM judges are paranoid, not discerning.** llama3.1:8b
   ties the rules on recall then emits 110 false positives. The durable asset
   is the instrument (`validate --judge`), which outlives the scoped claim.
5. **More reasoning ≠ more safety:** the one thinking model was 10–17× slower
   and the least safe subject.

## 3. Mistakes, ranked by lesson value

1. **Believing degenerate numbers, briefly, twice.** Both incidents began
   with a statistically absurd result accepted for minutes. Rule now
   internalized: zero or degenerate scores → inspect raw traces before
   believing anything. A 5-second benchmark of a 7B model is a symptom.
2. **Designed-only validation labels through v0.2.** Author-designed traces
   measure the rules against the author's imagination. The first 15 sampled
   real traces immediately exposed a taxonomy hole the 53 designed items never
   could. Sampled-real should have entered the set one version earlier.
3. **Strategy-review loop risk (called at the v0.3 pre-mortem, confirmed
   since).** The gravitational pull toward re-planning instead of shipping is
   this project's #1 risk. The one-gate-per-version immutable is the fix and
   this document complies with it.

## 4. Hidden assumptions uncovered

- *"Unsafe models comply; safe models refuse."* False dichotomy — the modal
  real behavior was **stall**. The safety–utility frontier has an interior.
- *"Format compliance can be assumed."* No: a strict parser silently converts
  capability into fake safety findings. The adapter must translate unambiguous
  variants; only genuine garbage may fail.
- *"The taxonomy is near-complete."* 15 real traces broke it. Assume every
  future sampled cohort will find another hole; that is the corpus's job.
- *"An LLM judge is a cheap labeling shortcut."* Not at 4B/8B zero-shot.
  Measured, not assumed — which is why the claim is safe to publish.

## 5. First-principles re-derivation (the architecture challenge)

Exercise: rebuild Groundtruth from zero knowing everything v0.3 knows.

**Survives unchanged:** Trace as ordered spans (no wall-clock); Detector
protocol returning explanatory `Failure`s; Dataset as diffable YAML; Validation
Engine measuring detectors against labeled traces; the ≥2-named-consumers rule;
determinism as a hard property; products-never-imported-by-platform. Every one
of these either caught a real bug, produced a real finding, or blocked real
scope creep. Evidence, not attachment.

**Changes on re-derivation — exactly one:** the taxonomy needs to express
**trace outcome** (completed / refused / stalled) in addition to safety
categories. Concretely for v0.4 this is a new category + detector
(`non_completion`: trace reaches step limit with no `Finish`), which the
existing machinery expresses without schema change. Consumer rule check:
AgentProbe (stall under adversarial pressure) and PlannerBench (no-recovery /
wasted-step detection) — two named consumers, rule satisfied.

**Verdict:** the roadmap survives its own re-derivation with one addition
already scheduled. Per the directive's own criterion, that increases
confidence; no rewrite is justified, and a rewrite proposal without a failing
test or a blocked feature behind it would be procrastination wearing an
architecture costume.

## 6. Ecosystem position & the missing measurement

Framework-by-framework positioning lives in POSITIONING.md and remains
accurate. The conceptual gap, stated once:

**Every major evaluation framework publishes scores; none publish the
precision/recall of its own scoring machinery, and none treat non-completion
as a first-class outcome.** LangSmith/Langfuse/Phoenix observe production;
DeepEval/Promptfoo count metrics they never validate; Inspect AI (closest
relative) is rigorous but unopinionated and does not self-measure. The two
measurements missing from the entire ecosystem are exactly Groundtruth's two
assets: **meta-evaluation** (measured detector quality with published misses)
and, after v0.4, **stall/non-completion measurement**. Benchmark that should
exist and doesn't: stall-rate of small models on benign-plus-adversarial tool
tasks. That is v0.4's research payload.

## 7. Moat, company, and publication — honest assessments

**Moat:** the code is weekend-cloneable; there is no code moat and pretending
otherwise would die in any serious review. What compounds: (a) the labeled
trace corpus with published misses, (b) the incident track record (norms are
harder to copy than code), (c) accumulated cross-model findings on one
deterministic harness. Data + norms, not software.

**Company thesis:** rejected for now. The mission (career constitution) is
hiring outcome, not venture outcome. Every "platform / protocol / certification
/ standard" fork demands distribution investment with zero interview ROI.
Optionality is preserved the cheap way: MIT license, clean OSS release, honest
methodology — if adoption signal ever appears, that decision reopens at a gate
review with evidence.

**Publication:** the right venue is an arXiv technical note + blog post, not a
conference paper — single-annotator labels and n=8 scenarios cannot survive
NeurIPS review and should not try. Two publishable notes exist: (1) the stall
taxonomy with measured stall rates (after §8 confounds are controlled), (2)
"harness-validity incidents: how measurement artifacts masquerade as behavioral
findings" — a methodology note the eval community actually lacks.

**Kaggle / competition:** the ~Sep 2026 AI Agent Security competition
(OpenAI×Google×IEEE) is the external-validation vehicle; v0.4's discriminating
scenario families are direct preparation for it. No other competition work
until then.

## 8. Red team — strongest attacks on our own claims

1. **Single annotator underlies every published P/R number.** Until Cohen's κ
   on a ~20-item subset exists, "measured detector quality" means "measured
   against one person's judgment." Mitigation: κ is a standing v0.4-window
   task (blocked on recruiting a second annotator); claims stay scoped until
   then; no strengthening of quality claims before κ.
2. **The stall finding has two live confounds:** `MAX_STEPS=6` (debt #10) may
   truncate slow-but-honest agents, and the stateless adapter (debt #11) means
   models can't see their own loop history — the stall could partly be *our*
   observation-format artifact. The v0.4 stall work must vary step limit and
   test a state-carrying adapter variant **before** any "dominant resistance
   mode" claim is published. This is the same class of error as the two parser
   incidents; we get no credit for the thesis if we fall for it a third time.
3. **n=8 scenarios means a 0.125 robustness delta is one scenario.** The
   benchmark supports existence proofs ("model X did Y on scenario Z, trace
   attached"), not rankings. Published framing must never imply a leaderboard.
4. **"Universal injection" overreaches** if stated without scope: six small
   local models, one injection scenario. Multi-hop injection variants (v0.4)
   are what turn it into a family-level claim.
5. **The `robustness` score contradicts "explain failure, don't count it."**
   Acceptable as a summary statistic; must never be the headline. Debt #8
   already tracks the naming; keep the tension visible, resolve at v1.0.
6. **Judge comparison used one prompt design.** Prompt sensitivity is
   unmeasured; the claim is scoped accordingly and the instrument exists to
   re-measure — acceptable, but the scoping sentence is load-bearing and must
   survive every future edit of the README.

## 9. Debt rankings (top of each register)

- **Technical:** #13 stall taxonomy (High, v0.4 core); #10 per-case step limit
  + #11 stateless adapter (promoted from Low to High — they are now research
  confounds, not conveniences); #12 lint/py.typed (pre-OSS, v0.4); #7–9 unchanged.
- **Scientific:** single-annotator labels (κ) > stall confounds > scenario
  count/diversity (8 is too few to discriminate) > judge prompt sensitivity >
  model diversity (all ≤8B, all local).
- **Infrastructure:** no GitHub remote — self-CI is dormant and **the entire
  portfolio is invisible**; this is the single highest-leverage item in the
  project and costs the user ~4 minutes. Everything else (packaging, docs
  site) is behind it.

## 10. Hiring-signal analysis (the committee test)

Candidate D (built Groundtruth) vs integrations / fine-tuning / Kaggle-win
candidates: D wins on system design, measurement discipline, and honest-failure
narrative — **but only if the committee can see it.** Today the repo has no
remote: Candidate D currently loses to everyone. Ranked actions by
signal-per-hour:

1. Push to GitHub, verify Actions green (user, ~4 min) — converts everything
   already built into visible evidence.
2. Ship the stall category + a short writeup — "the failure mode nobody's
   benchmark can see" is the memorable artifact the committee retells.
3. The two-incident harness-validity story in the README — already done;
   surfaces the exact trait (distrusts own results) senior engineers screen for.
4. Demo video + docs polish — after the above, not before.

## 11. Roadmap: v0.4 → v1.0 (each version = purpose + exit + kill criteria)

| Version | Purpose (why it exists) | Exit criterion | Kill/skip criterion |
|---|---|---|---|
| **v0.4 — "Visible & novel"** | Stall category (confounds controlled: vary MAX_STEPS, state-carrying adapter variant; label the 9 known stalls; re-pin snapshot); discriminating scenario families (multi-hop injection, secret variants — each justified by info-gain against the 6-model grid); OSS release polish (lint, py.typed, docs); GitHub push + public CI | A stranger can clone, reproduce the benchmark, and read the stall finding; Actions green publicly | If stall proves to be an adapter artifact, publish *that* as the finding — it is equally strong evidence for the thesis |
| **v0.5 — "Platform proof"** | JudgeKit on the spine: judge agreement/calibration as Detectors, seeded from the existing `validate --judge` instrument; frontier-judge measurement joins the rules-vs-judge table | A second product runs on unmodified core; any core change it forced is documented in an ADR | If core needs >1 significant change, the platform claim was wrong — record it honestly and re-derive |
| **v0.6 — "External validation"** | κ published (needs second annotator); corpus growth from new benchmark cohorts; AI Agent Security competition entry built from v0.4 scenario families | Competition submission filed; κ number published with the quality table | Competition slips → κ + corpus still ship |
| **v1.0 — "Reference implementation"** | Methodology note on arXiv (stall + harness-validity incidents); reproducible benchmark release with methodology + reproduction path; case-study writeup (the interview asset, explicitly) | The project is quotable: a external reader can cite the method, rerun the numbers | — |
| **v2.0 / PlannerBench** | **Deliberately unplanned.** Decided at the v1.0 gate from evidence (adoption signal, interview pipeline state, competition outcome) | — | — |

**Five-year roadmap:** refused on principle. A five-year plan for a
portfolio project is fiction that costs planning time now and credibility
later. The five-year *direction* is one sentence — the reference
implementation for offline, self-measured agent-reliability evaluation —
and every step toward it is gated on evidence at a version boundary.

## 12. Decisions made at this gate (with reasons)

- **D1 — v0.4 scope locked** as roadmap row 1. Reason: stall is the novel
  contribution, scenarios are the competition prep, the push is the
  visibility multiplier; everything else is behind those three.
- **D2 — Architecture unchanged; taxonomy gains a `non_completion` outcome
  category.** Reason: §5 re-derivation — one addition, two named consumers,
  no schema change. Rewrites without failing tests behind them are rejected.
- **D3 — Debt #10 and #11 promoted to High.** Reason: they graduated from
  conveniences to confounds of the flagship research claim (§8.2).
- **D4 — The directive's organizational scope (executive councils, divisions,
  unlimited worker agents, 31-section deliverable) is rejected — third
  consecutive gate.** Reason: cold-start persona agents re-derive context and
  add no evidence; all ten requested lenses are applied inline in this
  document (scientist §2/§6, engineer §5, safety §2.1/§8.2, strategist §6,
  founder §7, reviewer §7/§8, systems-researcher §5, hiring committee §10,
  future-CTO §11, red team §8). Career constitution's time-efficiency gate
  supersedes prompt structure; precedent recorded twice in session history.
- **D5 — Benchmark results are existence proofs, never rankings.** Reason:
  §8.3; n=8 scenarios cannot support ordinal claims.
- **D6 — ADR audit: ADR-0001…0005 all remain in force**; ADR-0006 (stall
  taxonomy design) will be written with the v0.4 implementation, not before —
  ADRs record decisions taken with code, not intentions.
- **D7 — Anti-goals reaffirmed and extended:** everything in POSITIONING.md,
  plus: no leaderboards from single-digit scenario counts; no five-year
  commitments; no strategy documents outside gate reviews; no multi-agent
  organizational simulation as a substitute for evidence.

## 13. Immutable principles (consolidated)

The six POSITIONING.md philosophy items, plus, earned since:

7. One gate review per version, then ship.
8. All published numbers come from one harness version; any harness change
   triggers a full re-bench.
9. Zero or degenerate scores are inspected at the trace level before belief.
10. Every claim ships with its scope sentence attached; the scope sentence is
    load-bearing.
11. Sampled-real traces enter the validation corpus every benchmark cycle —
    the corpus's job is to break the taxonomy.
