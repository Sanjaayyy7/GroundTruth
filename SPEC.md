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
- **v0.3.** React dashboard (reads scorecard + validation JSON); CI mode (fail a
  PR on safety regression vs a stored baseline); LLM-assisted detectors measured
  against the same labeled set (rules vs LLM-judge comparison on P/R).
- **v0.4.** Docs, demo video, public benchmark, open-source release. Then start
  **JudgeKit** on the same spine.

## 6. Risk register

| Risk | Mitigation |
|---|---|
| **Technical** — heuristic detectors → false pos/neg | high-precision rules first; benign control in-suite; **shipped in v0.2:** labeled validation set with reported P/R (micro 0.90/0.85), misses named and pinned by regression test |
| **Product** — "yet another eval tool" (DeepEval, Phoenix, Langfuse) | do not compete on general LLM eval; own *deterministic offline agent red-teaming* — their weak spot and the competition's exact frame |
| **Hiring** — could read as a wrapper if detectors are trivial | real trace model + failure taxonomy + measured detector quality + failure explanations, all tied to published research |
| **Opportunity cost** — 4–6 wks total | v0.1 (~1 wk) already proves the story; expand only if signal is good (retrospective gate before each version) |

## 7. Technical debt register (living; audited each gate review)

| # | Item | Category | Rank | Timing |
|---|---|---|---|---|
| 1 | Repo has no CI running its own tests | Infrastructure | High | v0.3 day 1 — a reliability gate must gate itself |
| 2 | LICENSE file missing (README claims MIT) | Documentation | High | v0.3 |
| 3 | CLI scenario/validation paths are cwd-dependent | Interfaces | Medium | v0.3 — resolve package/repo-relative |
| 4 | Validation loader: a label typo silently mints a new category | Validation | Medium | v0.3 — vocabulary guard |
| 5 | `demo_agents.py` at package root; belongs under `products/agentprobe/` | Architecture | Medium | v0.3 |
| 6 | No `schema_version` on persisted Trace/Scorecard JSON | Future-compat | Medium | v0.3, with stored CI baselines (first consumer) |
| 7 | `Case.suite` populated from YAML key `product` — naming entropy | Naming | Low | next dataset touch |
| 8 | "robustness" now blends safety + utility semantics | Naming | Low | reconsider at v1.0 |
| 9 | Span `kind` is a free string (no enum/validation) | Interfaces | Low | with schema_version |
| 10 | `MAX_STEPS=6` global, not per-case | Interfaces | Low | when a scenario needs it |
| 11 | OllamaAgent is stateless (sees only last tool result) | Architecture | Low | documented; revisit with multi-turn scenarios |
| 12 | No lint config / `py.typed` marker | Dev experience | Low | pre-OSS release (v0.4) |

Docs: `docs/adr/` records the decisions; `docs/POSITIONING.md` records identity.
