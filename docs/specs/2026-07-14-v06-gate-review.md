# v0.6 Gate Review — Meta-Evaluation Engine

Seven lenses, applied inline (consistent with every prior gate: no persona
agents). Each lens: what became stronger, what assumptions remain, what
should never be built, single next milestone. Every statement cites a repo
artifact. Baseline at gate: 116/116 tests, `groundtruth audit` rc 0,
published detector numbers byte-unchanged (P 0.9333 / R 0.8936,
runs/detector-quality.json).

## 1. Architecture

- **Stronger:** the canonical layering exists in code, not just diagrams —
  `loader → model ← graph ← contracts ← {manifest, assurance}`; only
  loader.py performs I/O (verifiable: `grep -rn "open(\|read_text\|subprocess"
  groundtruth/meta/` hits loader.py only, plus json import in manifest for
  rendering). Manifest and assurance are true siblings (no cross-import).
  ADR-0006 records the placement, the one-loader guardrail, and the
  generalization trigger.
- **Assumptions:** register formats (claims v2 / threats v1) are stable
  enough for a future JudgeKit to adopt; untested until a second consumer.
- **Never build:** loader plugin systems, evidence-provider interfaces, a
  graph database. The trigger for any generalization is JudgeKit's actual
  registers, not anticipation.
- **Next milestone:** JudgeKit's first register emission — the cheapest
  possible second consumer of the formats.

## 2. Scientific

- **Stronger:** claims can no longer silently drift from their evidence.
  Negative control verified at implementation: a planted metric lie
  (0.9333→0.9999) produced `[CT5] claim:C6 …` and rc 1; restored, rc 0.
  Pre-registration is now git-verified (loader checks 040c804 is an
  ancestor of 1bcfe31; manifest D10 lists claim:C3).
- **Assumptions:** the contracts check linkage and consistency, not truth —
  a wrong-but-consistent register passes. Single-annotator labels remain the
  top weakness (threats.yaml S2, surfaced in D04 and the assurance report).
- **Never build:** a composite quality score. Stated in the manifest itself
  (`no_composite_score`), tested (`test_no_composite_score_anywhere`),
  and recorded in ADR-0006 Rejected.
- **Next milestone:** inter-rater κ (unblocks D04; every P/R claim currently
  carries the single-annotator caveat).

## 3. Research

- **Stronger:** the reviewer question "why do you claim X?" now has a
  mechanical answer: follow the evidence graph (58 nodes / 63 edges at this
  commit) from claim to artifacts to version. Positioning is
  evidence-mapped with gaps stated (RESEARCH_POSITIONING.md v0.6 table);
  best-supported framing: "an agent-evaluation framework that audits its own
  evidence," with "Evaluation Assurance Platform" earned only after a second
  consumer.
- **Assumptions:** that meta-evaluation is a differentiator reviewers care
  about; plausible (evals-of-evals is an active gap) but unvalidated
  externally.
- **Never build:** a public "Evidence Operating System" thesis before a
  second product consumes the evidence infrastructure (ADR-0006 keeps it an
  internal direction).
- **Next milestone:** the arXiv-style methodology note — the stall artifact +
  three harness incidents + the audit apparatus is now a complete,
  reproducible story.

## 4. Product

- **Stronger:** `groundtruth audit` is a real CLI surface with honest exit
  semantics (0/1/2, tested in test_cli.py) and two consumable artifacts
  per run. README documents it without changing the headline (gated).
- **Assumptions:** anyone besides Groundtruth wants to audit an evaluation
  this way; the register-authoring cost (threat_refs, metrics, dimension
  tags) is the adoption tax and it is nonzero.
- **Never build:** dashboards or visualization for the graph; the artifacts
  are files by design (offline, diffable, CI-native).
- **Next milestone:** GitHub push + public CI green — the entire trust
  apparatus (v0.5 docs + v0.6 audit) is invisible until it runs in public.
  Still user-blocked, still ~4 minutes, now 5+ gates outstanding.

## 5. Technical debt

- **Stronger:** debts #1/#10/#13-adjacent guarantees are now continuously
  enforced rather than point-in-time (CT6 version stability, CT1 evidence
  resolution). Debt register updated in SPEC.md §7 (rows 14–16).
- **Assumptions:** README version regex (`**vX.Y — shipping**`) is a
  convention, not a schema; a format change fails loudly (CT6) rather than
  silently, which is the acceptable failure mode.
- **Never build:** contract auto-fixers. A finding must be resolved by a
  human editing the register or the doc — the audit polices, never rewrites.
- **Next milestone:** derive D05 (dataset discrimination) from scorecards —
  the one dimension still `documented` rather than `machine`.

## 6. Staff engineer

- **Stronger:** 6 new modules, all pure except one loader; 38 new tests
  (116 total, from 78); every meta test runs without filesystem or git
  except loader/CLI tests, which use tmp fixtures with real `git init`.
  Zero new dependencies. Zero changes to measurement code — published
  numbers provably untouched (validate output identical).
- **Assumptions:** contract set (CT1–CT10) is the right minimal set; CT
  additions are cheap (one pure function + one planted-violation test).
- **Never build:** meta/ abstractions ahead of the second consumer — the
  ARB's own warning, now enforced by ADR-0006's review trigger.
- **Next milestone:** run `groundtruth audit` against a deliberately broken
  historical commit as a fixture — regression-proof the negative controls.

## 7. Interview ROI

- **Stronger:** the one-liner is now demonstrable in 90 seconds: break a
  number in claims.yaml, run `groundtruth audit`, watch CI fail with a named
  explanatory finding, show the assurance report separating facts from
  provisional observations. That demo is the portfolio differentiator —
  nobody else's eval repo fails its own build over an evidence mismatch.
- **Assumptions:** panels value epistemic infrastructure as much as model
  results; the RESEARCH_POSITIONING skeptic descriptions remain the honest
  pitch calibration.
- **Never build:** breadth-for-optics (more scenarios, more models) before
  the κ study and the public push — trust compounds, size doesn't.
- **Next milestone (the single highest-ROI item across all lenses):**
  **GitHub push + public CI green** (user, ~4 min), then the multi-hop
  scenario family already justified by DATASET_AUDIT.

## Verdict

v0.6 ships. The milestone converted v0.5's hand-written trust apparatus into
machine-enforced infrastructure without touching a single published number.
The repository can now answer "why should anyone trust this evaluation?"
with an auditable chain instead of an essay — and it fails its own build
when that chain breaks.
