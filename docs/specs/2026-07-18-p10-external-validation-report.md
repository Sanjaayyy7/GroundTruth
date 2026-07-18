# Phase 10 Report — External Validation Pipeline (Local Recruiter-Clone Simulation)

**Date:** 2026-07-18
**Protocol:** `docs/specs/2026-07-18-p10-external-validation-protocol.md` (committed 15abf5c, before measurement)
**Repo state measured:** clean clone of 15abf5c into isolated scratch directory
**Mode honored:** measure only — zero files changed in the repository during execution.

## 1. Verdict

**H-P10 is FALSIFIED** — by exactly one persona checkpoint (OSS maintainer:
no contribution path), as pre-registered prediction P5 said it would be.
Every other persona succeeded within budget. **All five pre-registered
predictions confirmed (5/5).** The method's negative control fired.

The engineering claims survived a stranger's reproduction untouched. The
failures found are *packaging and voice* failures, not engineering failures.

## 2. Clean-Clone Reproduction Log (P1: CONFIRMED)

Environment: macOS, `python` → Python 3.13.5 (author's venv is 3.11 —
cross-version reproduction). Every command verbatim from README in order.

| # | Command | rc | Wall clock | Observation |
|---|---|---|---|---|
| 1 | `python -m venv .venv` | 0 | 1.2 s | see F9 |
| 2 | `pip install -e ".[dev]"` | 0 | 2.2 s | no warnings beyond pip self-update notice |
| 3 | `groundtruth run --agent vulnerable_agent` | 0 | 0.4 s | **robustness 0.25** — matches README exactly |
| 4 | `groundtruth run --agent hardened_agent` | 0 | 0.06 s | **robustness 1.00** — matches |
| 5 | `groundtruth run --agent paranoid_agent` | 0 | 0.05 s | **robustness 0.75** — matches |
| 6 | `groundtruth run --agent ollama:gemma3:4b` | 0 | live model | worked (Ollama running locally; see F3/F4) |
| 7 | `groundtruth validate` | 0 | 0.09 s | misses shown as promised (`ut_pos_04_semantic_gap`) |
| 8 | `groundtruth ci --agent hardened_agent` | 0 | <1 s | "baseline 1.0 → current 1.0, no regression" |
| 9 | `groundtruth report` | 0 | <1 s | HTML written, 12 subjects |
| 10 | `groundtruth steward` | 0 | <1 s | green on fresh clone |
| 11 | `pytest -q` | 0 | 10.8 s | **168 passed** |

**Zero undocumented steps. Zero deviations required.** Total compute for the
entire quickstart: under 30 seconds.

RC8 live demo (README lines 74–76) reproduced exactly: append one byte in
`examples/minijudge/README.md` → steward rc 1 with
`[RC8] examples/minijudge/README.md: frozen tree modified since 3d294a37356f`
→ revert → rc 0.

`git status` after all eleven verbs: **empty**. No verb dirties the tracked tree.

Time-to-first-success: 3 commands, ~4 s of compute past clone.
Time-to-full-verification (suite green): 11 commands, <30 s compute.

## 3. Persona Results

| Persona | Budget | Result | Evidence |
|---|---|---|---|
| Technical recruiter | README top ~40 lines | **PASS** | identity in lines 1–16 (platform + product table); first trust artifact lines 20–39 (machine-readable claims register + audit) — P2 confirmed |
| Hiring manager | README only | **PASS** | scope (3 products, 1 shipped), maturity (v0.8), measurable results (robustness table L137–143, detector P/R table L209–215) all README-resident |
| Staff AI engineer | ≤10 file opens | **PASS in 4 opens** | README → SPEC.md → `groundtruth/` listing (adapters/core/meta/products/steward mirrors diagram) → ci.yml; honest limitation (E6) found at hop 0, README line 55 |
| Applied AI engineer | README + commands | **PASS** | working CLI in 3 commands (§2) |
| Research engineer | ≤6 hops | **PASS in 2 hops** | README L70–73 → stewardship protocol / validation report; report contains 10 control references + commit pins — P4 confirmed |
| OSS maintainer | root + docs listing | **FAIL** | LICENSE present, ci.yml present; `CONTRIBUTING.md` absent, `.github/ISSUE_TEMPLATE` absent — P5 confirmed |

Method negative control (§2.4 of protocol): the CONTRIBUTING.md probe produced
a logged friction finding → the walkthrough method is capable of failure →
run valid.

## 4. Friction Inventory (P3: CONFIRMED — 9 findings, predicted ≥3)

Ordered by severity for public readiness. **None fixed in this phase.**

- **F1 — Internal career voice in the public tree.** "interview" appears
  **22 times across 13 tracked files**, including SPEC.md §1 ("the strongest
  single interview story on this market") and most specs' "Career ROI" sections;
  "career" appears 6 more times. A skeptical external engineer reading SPEC's
  thesis sees portfolio optimization before they see research. This is the
  single largest gap between internal artifact and public research artifact.
  Decision (keep-as-honest vs. relocate) belongs to Phase 13.
- **F2 — Version anchors disagree inside README.** AgentProbe is "v0.8 —
  shipping" (L9), "AgentProbe (v0.6)" (L78), and "(v0.4)" in the architecture
  diagram (L306). Three versions, one product, no disambiguation of platform
  version vs. product version. Steward runs green on this → the RC that checks
  version-anchor agreement does not cover product-version strings in prose.
- **F3 — Error-path quality.** `groundtruth run --agent ollama:no-such-model`
  exits 1 via a raw `urllib.error.HTTPError: HTTP Error 404` traceback. The
  first command a stranger personalizes is the one with the worst failure mode.
- **F4 — Ollama prerequisites undocumented.** README never states Ollama is
  optional, must be installed, or must be serving. A stranger without it hits
  quickstart line 4 with a connection traceback.
- **F5 — No CONTRIBUTING.md** (OSS-maintainer checkpoint failure).
- **F6 — No issue templates** (`.github/ISSUE_TEMPLATE` absent).
- **F7 — No CITATION.cff, no SECURITY.md.** A repo positioned as a research
  artifact provides no citation metadata.
- **F8 — Navigation load.** README is 312 lines with no table of contents;
  quickstart begins at line 96; `docs/` holds 16 entries with no index file.
  The applied-engineer path crosses 95 lines of research narrative before the
  first runnable command.
- **F9 — `python` vs `python3`.** Quickstart's `python -m venv` succeeded here
  only because a conda `python` shadowed the system; stock macOS ships
  `python3` only.

## 5. Unpredicted Findings (yield beyond the protocol)

- **U1 (magnitude of F1):** the protocol predicted friction, not that the
  largest class would be *voice*, nor its extent (13 files).
- **U2 (RC scope gap via F2):** README prose version strings sit outside
  steward's anchor contract — discovered only because a green steward coexists
  with a three-way version disagreement.
- **U3 (measurement discipline):** the evaluation harness itself produced two
  false exit-code readings during execution (piped `rc=$?` captured the pipe
  tail's status, not the verb's). Both caught by unpiped re-measurement; both
  re-measured values are what §2 reports. Recorded because a validation
  pipeline that can misread rc is itself a threat to validity.

## 6. Missing-Context Inventory

CONTRIBUTING.md · .github/ISSUE_TEMPLATE/ · CITATION.cff · SECURITY.md ·
docs/ index · README table of contents · Ollama prerequisite note ·
platform-vs-product version legend.

## 7. Recommendations (listed only — implementation requires a later phase)

1. Phase 13 decision on F1 (career voice): relocate strategy/ROI material out
   of the public tree, or reframe SPEC §1 — evidence says decide before push.
2. Fix F2 by choosing one versioning story and (candidate) extending the
   anchor RC to prose product-version strings.
3. F3/F4: friendly error + one README line on Ollama prerequisites.
4. F5–F7: standard public-repo files before or immediately after push.
5. F8: README TOC + docs/ index.
6. F9: `python3 -m venv` in quickstart.

## 8. Threats to Validity

Single evaluator with prior repo exposure (mitigated by verbatim-README
discipline and hop budgets, not eliminated); simulated personas, not humans;
reading-effort proxies, not human timing; Ollama present on this machine, so
the true no-Ollama first-run experience (F4) is inferred from the bogus-model
probe, not observed. Independent human replication remains the discharge
condition for this phase's E6-class limitation. U3 is disclosed above.

## 9. Phase Gate

Engineering reproduction: **stranger-proof as measured.** Public packaging:
**not ready** (F1–F9). Recommended next step per the Phase IV ordering:
GitHub push, then Phase 11 re-measures F-findings against the live repo before
any fixes, so the public baseline is recorded honestly.
