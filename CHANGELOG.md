# Changelog

One entry per shipped milestone, derived from the SPEC §5 roadmap record and
its milestone → ship-commit lineage table. No claim here is new: every line
condenses what SPEC §5 already records, with the full evidence chain in the
linked protocol and report documents. Commits after the `v0.8.0` tag are
publication hardening (external validation, error contracts, the public
baseline); they belong to no milestone and are visible in the git log.

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
