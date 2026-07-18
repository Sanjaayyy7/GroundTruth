# Groundtruth — Spec & Roadmap

Working design record for the Groundtruth platform. Locked for v0.1; revised at
each phase retrospective.

## 1. Thesis

The scarce, in-demand AI-engineering skill in 2026 is **evaluation and
reliability** — knowing *when and why* an AI system fails, offline and
reproducibly, before it ships. Groundtruth is that, built as one platform with a
family of products rather than three disconnected repos. AgentProbe is product #1
because "I built the offline agent-safety benchmark" is the strongest single
interview story on this market (mirrors the OpenAI × Google × IEEE *AI Agent
Security* competition and arXiv 2507.20526).

## 2. Architecture (locked)

Three-layer separation. **Platform** never imports **products**; products depend
only on the platform's public types.

```
Platform (groundtruth/core, groundtruth/adapters)
  Trace Engine      trace.py       ordered spans of a subject run (no wall-clock)
  Eval Engine       evaluator.py   Detector protocol + evaluate() -> Scorecard
                    scorecard.py   Failure taxonomy (the differentiator)
  Dataset Store     dataset.py     Case loaded from YAML; product fields in `spec`
  Validation Engine validation.py  labeled traces -> measured detector P/R (v0.2)
  Adapters          adapters/agent.py         Agent protocol: reset()+step()->Action
                    adapters/ollama_agent.py  any local Ollama model as a subject

Product (groundtruth/products/*)
  AgentProbe      runner.py     deterministic mocked-tool loop -> Trace
                  detectors.py  5 safety detectors -> explanatory Failures
```

### Every abstraction has a future consumer (the hard constraint)

| Primitive | AgentProbe | JudgeKit | PlannerBench |
|---|---|---|---|
| **Trace** | agent tool-run log | judge decision log | episode log |
| **Detector / Eval Engine** | safety detectors | agreement / calibration | efficiency / recovery |
| **Failure taxonomy** | injection, unsafe call | miscalibration, bias | wasted steps, no-recovery |
| **Dataset `Case`** | attack scenario | battle pair | task |
| **Agent adapter** | subject under test | judge model (wrapped) | subject under test |
| **Validation Engine** | detector P/R (shipped) | judge-vs-human agreement | detector P/R; CI gate (v0.3) |

No primitive is speculative — each already has ≥2 named consumers.

## 3. Failure taxonomy (the differentiator)

Detectors return `Failure`, never a boolean:

```
Failure(case_id, detector, category, severity, summary, chain[], recommendation)
```

`category` names the failure class; `severity ∈ {low, high, medium, critical}`;
`chain` is the human-readable causal sequence; `recommendation` is the fix. This
is what separates Groundtruth from "score = 72" eval libraries — we explain
failure, we don't just count it.

Categories: `unsafe_tool_invocation`, `instruction_hijacking` (v0.1);
`secret_exfiltration`, `goal_drift`, `over_refusal` (v0.2). `over_refusal` is
deliberate product thinking: it measures the *utility* side of the frontier, so
a maximally paranoid agent cannot score a perfect card by refusing everything
(the bundled `paranoid_agent` demo proves it: 0.75, failures all `over_refusal`).

## 4. Technology decisions

| Decision | Why | Rejected alternative |
|---|---|---|
| Python | agent ecosystem lives here | — |
| Agent adapter protocol (local + API) | runs on M4 Pro, $0 GPU, determinism | API-only (cost, non-reproducible) |
| YAML scenarios | diffable, git-native, reviewable | a DB (YAGNI at this scale) |
| Span/trace JSON shape | mirrors OTel — the production LLM-observability standard | bespoke format (no transfer value) |
| stdlib `argparse` + `pyyaml` only | tiny dependency surface for v0.1 | a CLI framework (premature) |
| deterministic mocked tools, no LLM in v0.1 | proves the harness reproducibly and free | LLM agent first (flaky, costly, hides harness bugs) |

Build-vs-buy: **buy/reuse** model serving (Ollama/MLX), charts (Recharts, later),
OTel trace concepts. **Build** the scenario schema, runner, detector framework,
and scorecard — the differentiated core.

## 5. Roadmap

- **v0.1 — DONE.** Platform spine + AgentProbe: schema, runner, 2 detectors,
  failure taxonomy, CLI, 5 scenarios (4 attacks + 1 benign control), e2e tests.
  Success criteria (all verified): vulnerable < hardened; hardened clean; no
  false-positive on control; deterministic.
- **v0.2 — DONE (2026-07-12).** Shipped:
  - **+3 detectors** (`secret_leak`, `goal_drift`, `over_refusal`) + `paranoid_agent`
    demo → the suite now exposes the full safety–utility frontier:
    vulnerable 0.25 / hardened 1.00 / paranoid 0.75 (8 scenarios).
  - **Validation Engine** (`core/validation.py`) + a 53-item hand-labeled trace set
    (`validation/agentprobe/`) with deliberately hard items. **Measured quality**
    (micro): precision **0.9032**, recall **0.8485**, f1 **0.875** — per-category
    numbers and every miss reported by `groundtruth validate` and pinned by a
    regression test. Known limits are named in the labeled set itself:
    name-matching misses semantic effects (`ut_pos_04`), declared-target rules miss
    off-target hijacks (`ih_pos_04`), no causality ordering (`ih_fp_01`), exact-match
    misses split/obfuscated secrets (`sl_pos_04/05`), no authorization concept
    (`sl_fp_01`), typo-retry counted as drift (`gd_fp_01`), phrasing-sensitive
    refusal matching (`orf_pos_03`).
  - **First real LLM subjects** via `adapters/ollama_agent.py` (stdlib-only,
    temperature 0 + fixed seed): `gemma3:4b` and `llama3.1:8b` both scored **0.88**
    — both obeyed an injected `SYSTEM:` instruction in a poisoned web-search result
    and invoked the forbidden `delete_files`. Scorecards in `runs/`.
  - Labeling methodology, honestly stated: traces authored + labeled by the
    developer (not third-party), with hard positives/negatives designed to expose
    rule limits; numbers are measurements of rule coverage on that set, not claims
    about attack-space coverage.
  - Deferred from v0.2: trace visualization (folds into the v0.3 dashboard).
- **v0.3 — DONE (2026-07-12→13; scope per ADR-0005; React dashboard demoted to a
  static report).** Part 1 shipped 2026-07-12: `groundtruth ci` regression gate
  (baseline compare, exit 1 on regression with newly-failing cases named);
  GitHub Actions workflow — the repo gates itself; `schema_version` on all
  persisted artifacts; LICENSE; cwd-independent CLI; demo agents moved under
  the product; label-vocabulary guard. Part 2 (2026-07-13): 6-model local
  benchmark on one harness version (llama3.1/3.2, mistral:7b, gemma3:4b,
  phi4-mini, qwen3:4b — indirect injection universal at 6/6; byte-identical
  rerun on the fastest model; raw traces persisted via `run --traces-out`);
  static self-contained HTML report (`groundtruth report`, escaped adversarial
  content, misses published); adapter parse fix after the first benchmark pass
  scored format non-compliance as over-refusal — documented in README as a
  harness-validity finding. Sampled-real cohort shipped: 15 traces (seed-42
  protocol, 2/model + 3 pool) labeled into the validation set → 68 items,
  micro P 0.9143 / R 0.8649 / F1 0.8889 (tp 32 / fp 3 / fn 5), snapshot-pinned;
  cohort exposed the loop-stall taxonomy gap (debt #13). Rules-vs-judge
  comparison shipped (`validate --judge`, LLM judge as an ordinary Detector):
  rules P 0.9143 / R 0.8649 / F1 0.8889 vs judge llama3.1:8b 0.2254 / 0.8649 /
  0.3576 (110 false positives) and gemma3:4b 0.3387 / 0.5676 / 0.4242 — small
  local judges over-flag massively; scoped to 4B/8B zero-shot judges,
  artifacts in runs/detector-quality-judge-*.json. Remaining: inter-rater
  agreement on a ~20-item subset (needs a second annotator); new
  discriminating scenario families (secret-leak and drift discriminate, benign
  controls and the universal injection don't).
- **v0.4 — DONE (2026-07-13→14; scope per docs/STRATEGY.md gate record).** Stall
  confounds resolved first, per the gate's evidence-before-detector rule
  (2026-07-13): pre-registered 5-cell experiment (stateless × 6/12/24 steps,
  stateful × 6/24; predictions committed before any run) replayed the 9 stall
  pairs + 2 controls. Result: stall is a **harness artifact of stateless
  observation** — 9/9 stalls persist at every stateless budget (temperature-0
  fixed point, byte-verified in traces), 0/9 survive one message of history;
  MAX_STEPS truncation contributes nothing; and 2 of 9 "safe stalls" become
  real injection compliance under state (llama3.2 exfiltrates to the
  attacker's address, mistral transfers funds and says so). Prediction P4
  (residual genuine stalls) falsified and published as such. Full report:
  `experiments/stall_confounds/REPORT.md`; raw evidence
  `runs/experiments/stall-confounds-2026-07-13/`. `non_completion` shipped
  same day (TDD; structural rule: no final span ⇔ budget exhaustion):
  corpus v2 labels the 10 budget-exhausted traces (9 stalls + qwen3's
  triple-compliance-without-answer), snapshot re-pinned to the numbers
  predicted before the relabel — micro P 0.9333 / R 0.8936 / F1 0.9130
  (tp 42 / fp 3 / fn 5), non_completion itself 10/0/0. Judge comparison
  stays scoped to corpus v1 labels (README scope note). Dual-condition
  re-bench shipped same day (`run --stateful` as a first-class flag; 12
  scorecards + raw traces in runs/): the six-detector suite inverts the v0.3
  ranking — llama3.1/3.2/mistral fall 0.875 → 0.0 stateless (their lead was
  stall-inflation), qwen3 (v0.3 last) unchanged at 0.625; under state all
  stalls vanish and secret_exfiltration goes 2/6 → 6/6 models (llama3.1
  emails the staging key to the attacker and repeats it in its answer).
  Deferred from v0.4: discriminating scenario families; lint/py.typed; GitHub
  push (user).
- **v0.5 — DONE (2026-07-14, scientific hardening; zero new features).** Seven
  review docs shipped (CLAIMS.md + claims.yaml with 10 classified claims,
  THREATS_TO_VALIDITY.md, REPRODUCIBILITY.md, DATASET_AUDIT.md,
  ARCHITECTURE_AUDIT.md, RESEARCH_POSITIONING.md); bootstrap 95% CI on
  detector quality (P [0.8448, 1.0000], R [0.7895, 0.9778], seed 42);
  fresh-venv reproduction verified byte-identical for both llama3.2
  conditions — determinism upgraded from "repeatable in practice" to fact (C9).
- **v0.6 — DONE (2026-07-14→15, meta-evaluation engine; spec
  `docs/specs/2026-07-14-v06-meta-evaluation-design.md`, gate review
  `docs/specs/2026-07-14-v06-gate-review.md`).** `groundtruth audit`:
  Evidence Loader (the one concrete YAML/filesystem/git adapter) → Evidence
  Model (`EvidenceNode`) → Evidence Graph (58 nodes / 63 edges) → ten
  Evaluation Contracts (CT1–CT9 pure invariants + CT10 byte-determinism,
  findings-not-scores) → two sibling assessments derived on every CI run:
  `runs/quality-manifest.json` (dimensions D01–D10, register-tagged, **no
  composite score**) and `runs/assurance-report.md` (per-conclusion
  justification, no aggregate verdict). Machine registers: threats.yaml
  (17 threats mirroring THREATS_TO_VALIDITY.md, CT8-locked) + claims.yaml
  schema v2 (threat_refs bidirectional per CT4, metric provenance per CT5,
  git-verified preregistration per D10, external-evidence markers per CT1).
  Negative control verified: a planted metric lie fails the build with a
  named finding. ADR-0006 records the layer, the one-loader guardrail, and
  the JudgeKit generalization trigger. 116 tests (from 78); published
  numbers byte-unchanged. Then **JudgeKit** on the same spine.
- **v0.7 — DONE (2026-07-15, external validation; protocol
  `docs/specs/2026-07-15-v07-external-validation-protocol.md`, outcome
  `docs/specs/2026-07-15-v07-architecture-validation.md`).** Single
  pre-registered question: can the Meta-Evaluation Engine audit an
  evaluation Groundtruth did not produce? Answer: yes, with zero
  modification to `groundtruth/meta/` (H1 confirmed; diff vs the protocol
  commit is empty). Second consumer: **MiniJudge**
  (`examples/minijudge/`) — a real 12-item judge-agreement evaluation
  (accuracy 0.75, script-generated artifact) with different domain,
  terminology, data format (JSON), and threat-ID family (`T…`), emitting
  the published register formats. The one predicted adaptation landed at
  the CLI surface only: `audit --name` (the manifest previously defaulted
  the evaluation name to "groundtruth" — pre-registered failure mode 1).
  14 new tests (130 total): green audit, consumer identity,
  byte-determinism, script-produced metric evidence, engine
  consumer-literal guardrail, 8 negative controls. CI audits both
  evaluations on every push; checkout now `fetch-depth: 0` (CT6/D10 break
  on shallow clones — latent v0.6 bug, pre-registered as failure mode 7).
  New claim C11 (preregistration 074bfb3 → 3d294a3, verified by D10);
  new threat E6 (same-author/same-repo independence limit). ADR-0007
  records what the second consumer proved. "Evaluation assurance
  platform" framing: still **not** earned — waits for an externally
  authored consumer (E6's future experiment).
- **v0.8 — DONE (2026-07-16→18, repository stewardship; protocol
  `docs/specs/2026-07-17-v08-stewardship-protocol.md`, validation
  `docs/specs/2026-07-18-v08-steward-validation-report.md`).** Convergence
  (`docs/specs/2026-07-16-v08-architecture-review-report.md`: 13 proposals
  → one advisory steward, 8 rejections evidence-cited) and governance
  tribunal (`docs/specs/2026-07-17-v08-governance-tribunal.md`: PROCEED
  WITH TARGETED REVISIONS R1–R7) preceded any code; the protocol was
  committed before implementation, v0.7 discipline. Shipped:
  `docs/CONSTITUTION.md` (13 laws — 9 ENFORCED with full
  law→test→CI→evidence chains, 4 JUDGMENT; declarations schema v1),
  `groundtruth/steward/` (RC1–RC8; stdlib-only, read-only enumerated git
  surface, byte-deterministic; 1,185 lines incl. tests under the
  1,496-line budget law), `groundtruth steward` CLI verb (rc 0/1/2),
  committed evidence in `runs/steward/`, debt migration to
  `docs/debt.yaml` (three pre-registered stale-state corrections
  confirmed; #17 closed by the CI diff step; #18–21 added by the
  scientific debt audit), blocking CI step after both audits. H1
  confirmed; honest zero at HEAD; 168 tests (from 130); ADR-0001's
  layering law mechanically enforced for the first time in 8 milestones.

Milestone → ship-commit lineage (tribunal R6; the archaeology gap — git log
carries every milestone string, but the mapping was previously tabulated
nowhere in-repo):

| Milestone | Ship commit |
|---|---|
| v0.1 | f243f9d |
| v0.2 | 615043a |
| v0.3 | 549f227 |
| v0.4 | ec9f56f |
| v0.5 | fa68ede |
| v0.6 | d6b3ba4 |
| v0.7 | a68c1c7 |
| v0.8 | in progress — recorded at gate review |

## 6. Risk register

| Risk | Mitigation |
|---|---|
| **Technical** — heuristic detectors → false pos/neg | high-precision rules first; benign control in-suite; **shipped in v0.2:** labeled validation set with reported P/R (micro 0.90/0.85), misses named and pinned by regression test |
| **Product** — "yet another eval tool" (DeepEval, Phoenix, Langfuse) | do not compete on general LLM eval; own *deterministic offline agent red-teaming* — their weak spot and the competition's exact frame |
| **Hiring** — could read as a wrapper if detectors are trivial | real trace model + failure taxonomy + measured detector quality + failure explanations, all tied to published research |
| **Opportunity cost** — 4–6 wks total | v0.1 (~1 wk) already proves the story; expand only if signal is good (retrospective gate before each version) |

## 7. Technical debt register

Lives in `docs/debt.yaml` (schema v1, evidence-backed, policed by RC7 —
Constitution Law 8). Migrated from this section on 2026-07-18; a prose
mirror is deliberately not kept (tribunal R4: prose state tables
measurably drift — the migration itself corrected three stale entries,
#11/#12/#13, exactly as the stewardship protocol pre-registered).

Docs: `docs/adr/` records the decisions; `docs/POSITIONING.md` records identity.
