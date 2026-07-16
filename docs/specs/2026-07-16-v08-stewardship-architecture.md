# v0.8 Repository Stewardship Architecture (converged, pre-implementation)

**Status:** architecture only — no implementation exists. Derived from
`docs/specs/2026-07-16-v08-architecture-review-report.md`. Implementation
may begin only after a pre-registered protocol (v0.7 discipline) and the
readiness review's recommendation.

## 1. Scope statement

One advisory subsystem that evaluates the repository the way the
Meta-Evaluation Engine evaluates registers: declarations in, deterministic
findings out, zero mutation. It answers six engineering questions (EQ1–EQ6
in the review report) and nothing else.

## 2. Layer placement

```
Platform      groundtruth/core, groundtruth/adapters      (measurement primitives)
Products      groundtruth/products/*                      (AgentProbe)
Meta          groundtruth/meta                            (audits evaluation registers)
Steward       groundtruth/steward                         (audits the repository)   ← new
CLI           groundtruth/cli.py                          (consumer surface for all layers)
```

Import law (enforced by RC5, including on the steward itself):

- `steward` imports **stdlib only**. Never core, products, meta.
- Nothing imports `steward` except `cli.py`.
- Existing laws unchanged: core never imports products; `meta/` stays
  isolated.

The steward parallels `meta/` — inside the package because the CLI ships
it and CI runs it; outside Core because it has one consumer (this
repository) and ADR-0001 forbids Core admission below two.

## 3. Module layout (planned, mirrors meta/'s shape)

```
groundtruth/steward/
  __init__.py
  model.py       Finding + RepoDeclarations dataclasses (~small; deliberately
                 duplicates meta/'s finding shape — documented, not shared)
  loader.py      parses the Constitution's declarations block + docs/debt.yaml;
                 collects the git index (read-only subprocess)
  inventory.py   git index × role rules -> repository manifest
  checks.py      RC1–RC8 pure functions: (declarations, inventory, contents) -> findings
  report.py      findings -> deterministic markdown report + JSON
```

Estimated size: same order as `meta/` (748 lines) including tests.

## 4. Evidence flow (read-only)

```
DECLARATIONS                          REPOSITORY STATE
docs/CONSTITUTION.md  ──┐             git index (ls-files)
  (embedded YAML block) │             tracked file contents
docs/debt.yaml        ──┤             git trees/commits (rev-parse, cat-file)
docs/adr/*.md         ──┘                    │
        │                                    │
        └────────────► steward ◄─────────────┘
                          │
              inventory (manifest) + RC1–RC8
                          │
        runs/steward/repo-manifest.json     (committed, byte-deterministic)
        runs/steward/steward-report.md      (committed, byte-deterministic)
                          │
        consumers: human maintainer · CI step · release procedure ·
                   future milestones (JudgeKit/PlannerBench inherit unchanged)
```

Allowed subprocess surface (exhaustive): `git ls-files`, `git rev-parse`,
`git cat-file`, `git diff --name-only <commit> -- <path>`, `git log
--format=%H -n1 -- <path>`. All read-only. Anything else is H0 evidence
under the implementation protocol.

## 5. The Constitution (docs/CONSTITUTION.md)

One file. Prose laws, each either naming its enforcing check (RC#) or
explicitly marked **JUDGMENT** (enforced by review, not code). One fenced
YAML declarations block parsed by `loader.py` — no companion config file,
so there is no prose↔config drift surface.

Declarations block schema (v1, versioned like the registers):

```yaml
constitution_schema: 1
roles:            # RC1 — first match wins, evaluated in order; final rule must be a catch-none
  - {pattern: "docs/adr/*.md",        role: adr,        lifecycle: living}
  - {pattern: "docs/plans/*.md",      role: plan,       lifecycle: historical}
  - {pattern: "docs/specs/*.md",      role: spec,       lifecycle: historical}
  - {pattern: "runs/**",              role: evidence,   lifecycle: derived}
  - {pattern: "examples/minijudge/**", role: consumer,  lifecycle: frozen}
  # ... exhaustive; RC1 fails on any unmatched tracked path
version_anchors: [...]        # RC3 — file + extraction pattern
derived_artifacts: [...]      # RC4 — path + regeneration command
frozen: [{path: examples/minijudge, commit: <freeze-commit>}]   # RC8
layer_rules: [...]            # RC5 — forbidden import edges
exemptions: []                # per-finding, each with a justification string; visible, diffable
```

Law drafts (final text at implementation; enforceable-first):

1. Advisory only — the steward never mutates (JUDGMENT + protocol).
2. Every tracked file has exactly one declared role (RC1).
3. References in living documents resolve (RC2). Historical documents are
   immutable records and exempt.
4. Declared version anchors agree (RC3).
5. Committed derived artifacts regenerate byte-identical (RC4 + CI diff).
6. Declared layer rules hold (RC5).
7. Accepted ADRs carry review triggers (RC6).
8. Debt lives in `docs/debt.yaml`, evidence-backed, never silently closed (RC7).
9. Frozen paths stay frozen; amendment requires editing the declaration
   with justification, in the same commit as the change (RC8).
10. A finding is resolved by fixing the repository or amending the
    Constitution with justification — never by weakening a check
    (JUDGMENT; mirror of the register law).
11. No abstraction before a second realized consumer (JUDGMENT; ADR-0001).
12. One hypothesis per milestone (JUDGMENT).
13. Release procedure: tests green, both audits rc 0, steward rc 0,
    working tree clean, RC4 diff clean. A checklist of existing commands —
    not code.

## 6. Document lifecycle classes (RC2 scoping)

| Class | Members | RC2 treatment |
|---|---|---|
| living | README, SPEC, CONSTITUTION, registers, accepted ADRs | policed |
| historical | docs/plans/*, dated docs/specs/*, shipped reports | exempt (immutable records; observed case: `tests/meta_fixtures.py` dangles only inside the v0.6 plan — correct to leave untouched) |
| derived | runs/**, examples/minijudge/runs/** | policed for freshness (RC4), not references |
| frozen | examples/minijudge/** | RC8; content immutable since declared commit |

Path-reference resolution order (from the second observed false positive):
resolve against the referencing file's directory, then the nearest
declared evaluation root, then the repo root. Only explicit markdown links
and backtick strings matching declared role patterns are candidates —
conservative by design; the protocol pre-registers the false-positive
budget.

## 7. Determinism rules (inherited from manifest.py conventions)

Sorted iteration everywhere; no wall-clock timestamps; no absolute paths;
LF newlines; content ordered by (check id, path, line). Two consecutive
runs on the same commit must be byte-identical — enforced by test, exactly
like the audit artifacts (CT10 parity).

## 8. CLI and CI

- `groundtruth steward [--root --out --json]` — rc 0 no findings,
  rc 1 findings, rc 2 declaration/usage error. Mirrors `audit`.
- CI: steward step runs **after** both audit steps (audit stays
  scientific; stewardship evaluates engineering — separate concerns).
  Blocking, symmetric with the audits: a finding means repository law is
  violated; the remedy is Law 10, never silencing. False-positive risk is
  carried by RC2's conservative scope + visible exemptions.
- Debt #17 closes in the same CI change:
  `git diff --exit-code runs/ examples/minijudge/runs/` after the audit
  steps (and after the steward regenerates its own artifacts).

## 9. Explicit non-goals

- No mutation, no auto-fix, no archiving/moving files.
- No scores, ranks, health grades, or "interest accumulation."
- No prediction. Observation and report only.
- No session/token telemetry; no attention or usage metrics.
- No NLP/semantic similarity of any kind.
- No generality for repositories other than this one (single realized
  consumer; ADR-0001 applied to the steward itself — generalization waits
  for a second repository that wants it).
- No shared findings library with `meta/`; the small model duplication is
  deliberate and documented in ADR-0008.
- No dashboards, web UI, plugins, schedulers, background agents.
- No absorption of lint/format/coverage/test tooling.

## 10. Interfaces frozen by this document

For the implementation protocol, these are the load-bearing surfaces:

1. Constitution declarations block schema v1 (§5) — versioned; changes
   follow the format-law discipline of ADR-0007 D2.
2. `docs/debt.yaml` schema v1 — id, title, category, state
   (open/resolved/accepted), origin version, evidence paths, resolution
   reference; **no numeric scoring fields**.
3. Steward artifact paths: `runs/steward/repo-manifest.json`,
   `runs/steward/steward-report.md`.
4. CLI verb + rc semantics (§8).
5. RC1–RC8 identities and one-line definitions (review report §4).
   Adding an RC9+ later requires the same evidence bar: a measured,
   currently-unenforced invariant.
