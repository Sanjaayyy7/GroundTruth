# Public Release Readiness Report — Repository Migration & Release Engineering Audit

**Date:** 2026-07-18
**Repo state audited:** main @ 87e91a4 (57 commits, 2026-07-12 → 2026-07-18)
**Mode:** audit and plan only. No repository content changed by this review.
**Companion baseline:** Phase 10 report (`2026-07-18-p10-external-validation-report.md`).

## 1. Repository Audit (Deliverable 1)

| Surface | Finding | Evidence |
|---|---|---|
| Commit history | 57 commits, 7-day span, conventional prefixes, engineering-intent subjects, no noise commits | `git log --format='%s'` — sample: `feat: RC1-RC8 checks + all eight pre-registered negative controls` |
| Commit trailers | **All 57 commits carry `Co-Authored-By: Claude Fable 5` trailers** | `git log --format='%(trailers:...)'` count = 57 |
| Tags / releases | **0 tags, no CHANGELOG, no releases** | `git tag | wc -l` = 0 |
| Branches | single `main` | `git branch -a` |
| Code hygiene | 0 TODO/FIXME/HACK/XXX; 0 debug prints outside CLI/report modules | grep across `groundtruth/ tests/` |
| Untracked | `SKILLS.md` only (assistant artifact, deliberately untracked — correct) | `git status --porcelain` |
| .gitignore | sane (venv, caches, egg-info, build, dist) | file inspected |
| ADRs | 8, numbered 0001–0008, present and titled | `ls docs/adr/` |
| CI | pins Python 3.11, 11 named steps incl. steward + byte-freshness diff; **never executed in cloud** (no remote has ever existed) | `.github/workflows/ci.yml` |
| Package metadata | `pyproject.toml` missing `license`, `authors`, `urls`, `classifiers`, `keywords` | file inspected |
| Tests | 168 passed (verified this session, 8.5 s) | pytest run at 87e91a4 |

## 2. Tool-Specific Artifact Review (Deliverable 2)

Objective per directive: the public tree contains only artifacts of the software
project itself — not to hide tooling, but to scope the repository.

- **T1 (largest):** `docs/plans/2026-07-14-v06-meta-evaluation-engine.md` —
  a 1,500+ line assistant execution plan. Line 3: "**For agentic workers:**
  REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development…"; contains
  six embedded `Co-Authored-By` commit templates. This is a development-
  environment artifact, not a project artifact. **Constraint:** it is
  referenced by `docs/CONSTITUTION.md` (role register — RC1 gives every
  tracked file a role) and two specs; relocation therefore requires a role/
  reference update and steward re-convergence, i.e. it is implementation, not
  deletion.
- **T2:** assistant-workflow phrasing ("no multi-agent spawns", "executed
  inline — no agent spawns") in `2026-07-14-v06-meta-evaluation-design.md`,
  the v06 plan, and `2026-07-18-p10-external-validation-protocol.md`.
- **T3:** `2026-07-16-v08-architecture-review-report.md:54` mentions "Claude
  attention / session telemetry" — inside a *rejected-question* record whose
  point is that non-reproducible evidence fails the scientific gate. Borderline:
  it is honest methodology, but it names the tool.
- **T4:** career-voice class from Phase 10 F1 — "interview" ×22 / 13 files,
  `docs/STRATEGY.md`, `docs/POSITIONING.md`, SPEC §1.
- **T5:** "orchestration directive" workflow references (11 in the v0.8
  architecture review report; also the governance tribunal spec).

**Recommendation only (no changes made):** decide T1 and T4 **before** push —
anything pushed is permanent in public history even if deleted later. T2/T3/T5
are lower-stakes honesty-vs-polish calls that can ride the post-baseline wave.

## 3. Git History & Release Plan (Deliverable 3)

Three candidate strategies were evaluated against the directive's own
constraints ("do not invent history", "do not create misleading timestamps",
"do not remove legitimate engineering evidence"):

| Strategy | Verdict | Evidence |
|---|---|---|
| **A. Push real history intact** | **RECOMMENDED** | history already exhibits every quality the directive demands: conventional commits, milestone coherence, TDD arcs, zero noise commits (§1). |
| B. Rewrite history to strip trailers | REJECTED | **26 unique commit hashes are pinned inside tracked documents** (SPEC §5 lineage, validation reports, debt evidence). `docs/CONSTITUTION.md:97` pins the RC8 frozen-tree base as a full 40-char hash — a rewrite invalidates every pin **and bricks the steward's RC8 check**. Cost: the entire inspectable-lineage asset. Gain: cosmetic. |
| C. Squash into milestone commits | REJECTED | destroys the TDD red-green arcs and protocol-before-implementation ordering that constitute the project's strongest methodological evidence; same pin breakage as B. |

**Trailer disposition:** existing 57 trailers remain (they are true authorship
metadata; removing them costs the evidence graph). New commits from
2026-07-18 onward follow the new standard: conventional format, engineering
intent only, no tool references, no trailers.

**Timestamps:** real dates stand. A 7-day intensive build is the honest record;
manufactured spacing would violate the misleading-timestamp constraint.

## 4. Release Structure Plan (Deliverable 4)

- Annotated tags at the historical ship commits (tags point at existing
  hashes — no rewrite): `v0.8.0` → f4fbb6e. Earlier milestone ship commits
  (v0.3–v0.7) tagged retroactively iff their ship commits are identified from
  SPEC §5 lineage; otherwise tag forward-only from v0.8.0.
- `CHANGELOG.md` derived from SPEC §5 lineage table — one entry per shipped
  version, content sourced from existing ship-commit messages and validation
  reports (no new claims).
- GitHub Release for v0.8.0 after push, body = ship-commit message + link to
  validation report.
- `pyproject.toml`: add `license`, `authors`, `urls`, `classifiers`.

## 5. Comment Review (Deliverable 5)

grep evidence: zero TODO/FIXME/HACK/XXX markers, zero debug prints outside
CLI/report modules, zero tool/conversation references in `.py` files
(`git grep -il claude -- "*.py"` = empty). Source comment surface passes the
gate; no per-file sweep warranted by evidence.

## 6. Documentation Consistency Audit (Deliverable 6)

- **F2 (open, blocking version-consistency gate):** AgentProbe appears as
  v0.8 / v0.6 / v0.4 in README lines 9/78/306. Taxonomy resolution (platform
  vs product version) is a Phase 13 architecture decision; the minimal
  coherent model is: *platform version is the only public version; product
  sections carry no version strings*.
- No CHANGELOG exists yet, so no CHANGELOG conflicts.
- Product naming consistent (AgentProbe/JudgeKit/PlannerBench).
- Version anchors README/SPEC/pyproject agree at 0.8.0 (steward-enforced).

## 7. Public Repository Standards Gap List (Deliverable 7)

Missing versus mature-OSS baseline (all confirmed absent by direct probe):
`CONTRIBUTING.md`, `CITATION.cff`, `SECURITY.md`, issue templates, PR
template, README table of contents, `docs/` index, package metadata (§1),
tags/releases (§4). Present and strong: LICENSE (MIT), CI definition,
deterministic committed artifacts, ADR trail, README quickstart (verified
stranger-proof in Phase 10).

## 8. Final Release Readiness & Publication Checklist (Deliverable 8)

Gates at 87e91a4:

- [x] Tests green — 168 passed (this session)
- [x] Deterministic artifacts byte-fresh — steward converged at commit
- [x] Working tree clean (SKILLS.md untracked by design)
- [x] History audit passed (§1, §3)
- [ ] **F1/T4 decision** — career voice: public-permanent once pushed
- [ ] **T1 decision** — assistant execution plan in public tree: public-permanent once pushed
- [ ] F2 minimal fix or accept-into-baseline decision
- [ ] Cloud CI verified (impossible until first push — becomes Phase 11 gate)
- [ ] Tags/CHANGELOG/metadata (§4 — post-decision, pre- or post-push)

## Go / No-Go

**CONDITIONAL GO.** Engineering gates all pass. Two decisions gate publication
because push makes them permanent: **F1/T4** (career voice) and **T1**
(assistant plan file). Everything else follows the Phase V sequence: push →
Phase 11 public baseline capture → fix wave. If the decision on both is
"keep — the repository is honest about how it was built", the repository can
push today with zero content changes.
