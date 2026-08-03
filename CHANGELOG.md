# Changelog

One entry per shipped milestone, derived from the SPEC §5 roadmap record and
its milestone → ship-commit lineage table. No claim here is new: every line
condenses what SPEC §5 already records, with the full evidence chain in the
linked protocol and report documents. Commits after the `v0.8.0` tag are
publication hardening (external validation, error contracts, the public
baseline); they belong to no milestone and are visible in the git log.

## v0.9.1 — 2026-08-03

Close three findings from the external technical due-diligence review that the
v0.9.0 pass left open. All three are the same shape: a guarantee the repository
stated in prose but never enforced in code.

- **`secret_leak` reported one sink per secret** (review finding A7). A
  credential copied into *both* an outbound tool call and the final answer was
  recorded once, and when the tool call came first the disclosure to the user
  vanished from the record entirely. Now deduplicated per sink rather than
  capped at one — a subject that loops the same call twenty times still leaked
  to that tool once. **Corrected 2 of 12 committed scorecards** (`llama3.1:8b`
  and `llama3.2` stateful, each `secret_exfiltration` 1 → 2, each gaining the
  missing `high`-severity answer disclosure). **No published rate moved**:
  `robustness_score` and `safety_rate` count cases, not failures, and both are
  unchanged at 0.25 and 0.375.
- **C5's breakdown was amended, its headline was not.** The claim read "3 send
  to the attacker address, 2 paste the key into the answer" — a breakdown that
  summed to 5 of 6 models and was produced by the under-count above. Re-measured:
  3 send to the attacker, **5** paste into the answer, **2 do both**. The
  2/6 → 6/6 headline counts models that leaked at all and is untouched.
- **Scenario keys are now vocabulary-guarded** (review finding A8, debt #22).
  Labels have been guarded since v0.2 while scenarios — the larger surface —
  were not, so a misspelled `completion_tools` loaded, ran, and scored clean
  with a detector contract silently dropped. `CaseSchema` is declared by the
  product and enforced in the core loader, because core must not learn what an
  AgentProbe scenario contains (ADR-0001, RC5-enforced). All violations in a
  file are reported in one pass.
- **`parse_action` has adversarial coverage** (review finding A6, threat I1,
  debt #23). The fail-open guarantee was previously mitigated by code reading.
  900 seeded inputs now assert it as a type. Stdlib `random` under a fixed seed
  rather than a property-based dependency: the one-runtime-dependency law is
  machine-checked, and a corpus that differs per run would make a failure
  unreproducible from the artifact alone.
- Test count 267 → 1187 (the fuzz corpus is parametrized). Runtime 11s.

## v0.9.0 — 2026-08-02

Close the loop: the most attackable published number was re-measured under a
pre-registered protocol, and the repository's own laws were extended to the
surfaces they had never reached.

- **Judge rerun, pre-registered** (`docs/specs/2026-08-02-judge-rerun-preregistration.md`
  → `experiments/judge_rerun/REPORT.md`). Four arms, two subjects, 68 items,
  same engine as the rules. The instrument was gated first: arm A0 reproduced
  the published `llama3.1:8b` precision exactly, id-for-id. Aligning the decode
  constraint with the prompt shape moved precision 0.2254 → 0.3600 and cut
  hijacking false positives 53 → 17, so C7's number was measured under a
  confound its scope never disclosed. **P4 was falsified**: removing the
  constraint made precision worse for both subjects, with zero parse failures,
  so the mismatch was the problem rather than the constraint. C7's ordering
  survives and its scope is corrected.
- **Two detector-semantics defects.** `instruction_hijacking` gained the causal
  precondition it always lacked; the corpus had already trapped the defect
  (`ih_fp_01_causality`) and the detector failed it. Removing that false
  positive moved micro precision 0.9333 → 0.9545. Published `by_category`
  counts were unchanged at 29 — the lens overlap is genuine, not inflation.
  `over_refusal` stopped discarding its own refusal signal.
- **Metric split** (debt #8, threat K1): `safety_rate`, `completion_rate` and
  `task_completion_rate` beside `robustness`, which is unchanged. The paranoid
  subject now scores 1.00 safety and 0.00 task completion.
- **Law 5 reaches its directory** (finding R4). `rescore` rebuilds any scorecard
  from committed traces; scorecards, the detector-quality report and the HTML
  report are declared derived and regenerated in CI. `report.html` had carried
  stale content through an entire detector change.
- **RC9**: numeric claims in living prose must resolve to a register or a
  reasoned allowlist entry. Declarations move to schema 2.
- **Trigger ledger**: each check's firing record ships in the manifest, so
  retirement triggers evaluate on evidence instead of on prose. Silent is
  recorded as silent, never as unnecessary.
- **The safety gate fails closed** on an unexplained improvement (finding D4).
- **debt #12 closes** after six milestones: ruff, mypy, `py.typed`, a Makefile,
  a pre-commit hook that converges derived artifacts to a fixed point, and a CI
  matrix on 3.11 and 3.12.
- README rewritten to 163 lines, opening with the finding; the long-form
  version is preserved whole at `docs/README-full.md`.

## v0.8.0 — 2026-07-18 (ship commit `f4fbb6e`)

Repository stewardship: the repository audits itself with the mechanics it
sells.

- [docs/CONSTITUTION.md](docs/CONSTITUTION.md) — 13 laws (9 ENFORCED with
  law→test→CI→evidence chains, 4 JUDGMENT), declarations schema v1.
- `groundtruth steward` CLI verb — eight repository contracts (RC1–RC8),
  read-only, stdlib-only, byte-deterministic; committed evidence in
  `runs/steward/`; blocking CI step diffs regenerated artifacts.
- Debt migrated to [docs/debt.yaml](docs/debt.yaml); three pre-registered
  stale-state corrections confirmed; debt #17 closed by the CI diff step.
- Convergence review and governance tribunal preceded any code; the protocol
  was committed before implementation.
- 168 tests. Protocol:
  [docs/specs/2026-07-17-v08-stewardship-protocol.md](docs/specs/2026-07-17-v08-stewardship-protocol.md).
  Validation:
  [docs/specs/2026-07-18-v08-steward-validation-report.md](docs/specs/2026-07-18-v08-steward-validation-report.md).

## v0.7 — 2026-07-15 (ship commit `a68c1c7`)

External validation: the unmodified Meta-Evaluation Engine audits an
evaluation Groundtruth did not produce.

- Second consumer **MiniJudge** (`examples/minijudge/`) — 12-item
  judge-agreement evaluation, different domain, terminology, data format,
  threat-ID family; audited green with zero modification to
  `groundtruth/meta/` (H1 confirmed).
- One predicted adaptation, at the CLI surface only: `audit --name`.
- CI audits both evaluations on every push; checkout `fetch-depth: 0`
  (latent v0.6 shallow-clone bug, pre-registered as failure mode 7).
- New claim C11 (git-verified preregistration), new threat E6 (same-author
  independence limit). 130 tests. ADR-0007.

## v0.6 — 2026-07-15 (ship commit `d6b3ba4`)

Meta-evaluation engine: `groundtruth audit`.

- Evidence Loader → Evidence Model → Evidence Graph (58 nodes / 63 edges) →
  ten Evaluation Contracts (CT1–CT10) → two derived assessments per CI run:
  `runs/quality-manifest.json` (dimensions D01–D10, **no composite score**)
  and `runs/assurance-report.md` (per-conclusion justification).
- Machine registers: [docs/threats.yaml](docs/threats.yaml) (17 threats) and
  [docs/claims.yaml](docs/claims.yaml) schema v2 (bidirectional threat refs,
  metric provenance, git-verified preregistration).
- Negative control: a planted metric lie fails the build with a named
  finding. 116 tests. ADR-0006.

## v0.5 — 2026-07-14 (ship commit `fa68ede`)

Scientific hardening; zero new features.

- Seven review documents: [docs/CLAIMS.md](docs/CLAIMS.md) with
  [docs/claims.yaml](docs/claims.yaml) (10 classified claims),
  [docs/THREATS_TO_VALIDITY.md](docs/THREATS_TO_VALIDITY.md),
  [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md),
  [docs/DATASET_AUDIT.md](docs/DATASET_AUDIT.md),
  [docs/ARCHITECTURE_AUDIT.md](docs/ARCHITECTURE_AUDIT.md),
  [docs/RESEARCH_POSITIONING.md](docs/RESEARCH_POSITIONING.md).
- Bootstrap 95% CI on detector quality (P [0.8448, 1.0000],
  R [0.7895, 0.9778], seed 42).
- Fresh-venv reproduction verified byte-identical for both llama3.2
  conditions — determinism upgraded from "repeatable in practice" to
  measured fact (claim C9).

## v0.4 — 2026-07-13 (ship commit `ec9f56f`)

Stall confounds resolved by pre-registered experiment; `non_completion`
shipped; dual-condition re-benchmark.

- Pre-registered 5-cell experiment (predictions committed before any run):
  stall is a harness artifact of stateless observation — 9/9 stalls persist
  at every stateless budget, 0/9 survive one message of history; 2 of 9
  "safe stalls" become real injection compliance under state. Prediction P4
  falsified and published as such. Report:
  `experiments/stall_confounds/REPORT.md`.
- `non_completion` detector (TDD; structural rule: no final span ⇔ budget
  exhaustion); corpus v2 → micro P 0.9333 / R 0.8936 / F1 0.9130,
  snapshot-pinned to numbers predicted before the relabel.
- `run --stateful` first-class flag; 12 scorecards + raw traces. The
  six-detector suite inverts the v0.3 ranking: stall-inflated leads fall to
  0.0; under state, secret exfiltration goes from 2/6 to 6/6 models.

## v0.3 — 2026-07-13 (ship commit `549f227`)

Regression gate, real-model benchmark, HTML report, judge comparison.

- `groundtruth ci` regression gate (baseline compare, exit 1 with
  newly-failing cases named); GitHub Actions workflow — the repo gates
  itself; `schema_version` on persisted artifacts; LICENSE; cwd-independent
  CLI.
- 6-model local benchmark on one harness version: indirect injection
  universal at 6/6; byte-identical rerun on the fastest model; raw traces
  persisted via `run --traces-out`.
- Static self-contained HTML report (`groundtruth report`), adversarial
  content escaped, misses published. Adapter parse fix after the first
  benchmark pass scored format non-compliance as over-refusal — documented
  as a harness-validity finding.
- Sampled-real cohort: 15 seed-42 traces labeled into the validation set →
  68 items, micro P 0.9143 / R 0.8649 / F1 0.8889; cohort exposed the
  loop-stall taxonomy gap (debt #13).
- Rules-vs-judge comparison (`validate --judge`): rules F1 0.8889 vs judge
  llama3.1:8b 0.3576 (110 false positives) and gemma3:4b 0.4242 — small
  local zero-shot judges over-flag massively.

## v0.2 — 2026-07-12 (ship commit `615043a`)

Full safety–utility frontier; measured detector quality; first real LLM
subjects.

- Three new detectors (`secret_leak`, `goal_drift`, `over_refusal`) and the
  `paranoid_agent` demo: vulnerable 0.25 / hardened 1.00 / paranoid 0.75 on
  8 scenarios.
- Validation Engine plus a 53-item hand-labeled trace set with deliberately
  hard items: micro precision 0.9032 / recall 0.8485 / F1 0.875, per-category
  numbers and every miss reported by `groundtruth validate` and pinned by a
  regression test. Known limits named in the labeled set itself.
- First real LLM subjects via `adapters/ollama_agent.py` (stdlib-only,
  temperature 0, fixed seed): gemma3:4b and llama3.1:8b both 0.88 — both
  obeyed an injected `SYSTEM:` instruction and invoked the forbidden tool.
- Labeling methodology stated honestly: developer-authored and
  developer-labeled; numbers measure rule coverage on that set, not
  attack-space coverage.

## v0.1 — 2026-07-12 (ship commit `f243f9d`)

Platform spine plus AgentProbe.

- Trace, Eval, Dataset engines; Detector protocol; explanatory failure
  taxonomy (category, severity, causal chain, recommendation — never a bare
  score).
- Deterministic mocked-tool runner, 2 detectors, CLI, 5 scenarios (4 attacks
  + 1 benign control), end-to-end tests.
- Success criteria all verified: vulnerable < hardened; hardened clean; no
  false positive on the benign control; deterministic reruns.
