# Repository Constitution

The laws this repository holds itself to, and the declarations that make
them checkable. Enforcement is the Repository Steward (`groundtruth
steward`, `groundtruth/steward/`): declarations in, deterministic findings
out, zero mutation — the same mechanics `groundtruth/meta/` applies to
evaluation registers, one layer up (ADR-0008). Laws marked **JUDGMENT**
are enforced by review, not code; every ENFORCED law names its check.

**Amendment rule:** edit the law or declaration *with justification, in
the same commit as the change it legitimizes*. Architectural laws
(marked ADR) additionally require an ADR. Evidence required to amend: a
finding, a falsified prediction, or a fired review trigger — never
preference.

## Laws

| # | Law | Origin | Enforcement | Retirement trigger |
|---|---|---|---|---|
| 1 | The steward is advisory and read-only: it never mutates the repository. | ADR-0008 | JUDGMENT + protocol zero-mutation test | Permanent (identity-level; amendment requires an ADR naming a replacement mechanism) |
| 2 | Every tracked file matches exactly one declared role rule; the rule list is catch-none — an unmatched path is a finding, not a default. | v0.8 review report EQ1 | RC1 | Role rules churn every milestone without catching anything |
| 3 | Path references in living documents resolve. Historical documents are immutable records and exempt. | EQ3 | RC2 | Sustained false-positive rate after scope fix (>2 forced exemptions in one milestone = scope surgery) |
| 4 | Declared version anchors agree (prefix-compatible, CT6 semantics). | EQ3 / CT6 superset | RC3 | Three consecutive silent milestones → demote into RC4's declaration check or retire (tribunal R5) |
| 5 | Every declared derived artifact carries a regeneration command and is tracked; CI diffs regenerated artifacts against committed copies. | EQ2 / debt #17 | RC4 + CI `git diff --exit-code` | Never fires after debt #17 closes |
| 6 | Declared import-layer rules hold: core never imports products; meta is isolated; the steward imports stdlib only; nothing imports the steward except the CLI. | ADR-0001, ADR-0008 | RC5 | Graph never changes and rules never fire |
| 7 | Every accepted ADR carries a `## Review trigger` section. | EQ on ADR liveness, halved per tribunal R1 | RC6 | ADRs stop being written |
| 8 | Debt lives in `docs/debt.yaml` (schema v1), evidence-backed, never silently closed: open/accepted items cite tracked evidence; resolved items cite a resolution reference that exists in git. | EQ6 / SPEC §7 drift measured at tribunal §1 | RC7 | Register abandoned for an external tracker |
| 9 | Frozen trees stay frozen: a declared frozen path must be byte-identical to its declared freeze commit; amendment = edit the declaration with justification in the same commit as the change. | ADR-0007 ("frozen forever") | RC8 | A legitimate freeze amendment happens more often than an accidental edit |
| 10 | A finding is resolved by fixing the repository or by amending the Constitution with justification — never by weakening a check. | v0.6 register law, mirrored | JUDGMENT | Permanent (identity-level) |
| 11 | No abstraction before a second realized consumer. | ADR-0001 | JUDGMENT | Permanent (per-case evidence bar) |
| 12 | One hypothesis per milestone. | v0.7 discipline | JUDGMENT | — |
| 13 | Release procedure: tests green, both audits rc 0, steward rc 0, RC4 diff clean, working tree clean. A checklist of existing commands, not code. | v0.8 convergence (Release Readiness merged) | JUDGMENT | — |

## Schema conventions (format law, versioned — ADR-0007 D2 discipline)

- Declarations block: `constitution_schema: 1`, exactly the keys `roles`,
  `version_anchors`, `derived_artifacts`, `frozen`, `layer_rules`,
  `exemptions`. A seventh key requires the RC9+ evidence bar and a schema
  bump with migration note.
- Pattern law: `**` crosses directories, `*` does not, `?` matches one
  non-separator character; rules evaluate in order, first match wins.
- Lifecycle vocabulary: `living` (policed by RC2), `historical`
  (immutable record, exempt), `derived` (freshness via RC4/CI, not
  references), `frozen` (RC8).
- Reserved role names: `code` scopes RC5's import scan; `adr` scopes RC6.
- RC2 resolution order: the referencing file's directory, then the repo
  root, then each declared frozen (evaluation-consumer) root. Only
  markdown links and backtick strings matching a declared role pattern
  are candidates; strings containing glob characters, spaces, or
  ellipses are templates, not references.
- Exemption entries carry `check`, `path`, `justification`, `milestone`.
  The steward report lists active count and age; review fires at ≥5
  active or any exemption older than 2 milestones (tribunal R3).
- Debt register: `debt_schema: 1`; items carry exactly `id`, `title`,
  `category`, `state` (open/resolved/accepted), `origin`, `evidence`,
  `resolution`. No numeric scoring fields — findings, never scores.

## Declarations (schema v1)

```yaml
constitution_schema: 1
roles:
  - {pattern: ".github/**", role: ci, lifecycle: living}
  - {pattern: ".gitignore", role: config, lifecycle: living}
  - {pattern: "CHANGELOG.md", role: doc, lifecycle: living}
  - {pattern: "LICENSE", role: legal, lifecycle: living}
  - {pattern: "README.md", role: doc, lifecycle: living}
  - {pattern: "SPEC.md", role: doc, lifecycle: living}
  - {pattern: "pyproject.toml", role: config, lifecycle: living}
  - {pattern: "docs/CONSTITUTION.md", role: law, lifecycle: living}
  - {pattern: "docs/adr/*.md", role: adr, lifecycle: living}
  - {pattern: "docs/claims.yaml", role: register, lifecycle: living}
  - {pattern: "docs/threats.yaml", role: register, lifecycle: living}
  - {pattern: "docs/debt.yaml", role: register, lifecycle: living}
  - {pattern: "docs/plans/*.md", role: plan, lifecycle: historical}
  - {pattern: "docs/specs/*.md", role: spec, lifecycle: historical}
  - {pattern: "docs/*.md", role: doc, lifecycle: living}
  - {pattern: "examples/minijudge/**", role: consumer, lifecycle: frozen}
  - {pattern: "experiments/**", role: experiment, lifecycle: historical}
  - {pattern: "groundtruth/**", role: code, lifecycle: living}
  - {pattern: "runs/**", role: evidence, lifecycle: derived}
  - {pattern: "scenarios/**", role: dataset, lifecycle: living}
  - {pattern: "tests/**", role: test, lifecycle: living}
  - {pattern: "validation/**", role: dataset, lifecycle: living}
version_anchors:
  - {file: "pyproject.toml", pattern: "^version = \"([^\"]+)\""}
  - {file: "README.md", pattern: "\*\*v([0-9.]+) — shipping\*\*"}
  - {file: "runs/quality-manifest.json", pattern: "\"version\": \"([0-9.]+)\""}
derived_artifacts:
  - {path: "runs/quality-manifest.json", regen: "groundtruth audit"}
  - {path: "runs/assurance-report.md", regen: "groundtruth audit"}
  - {path: "examples/minijudge/runs/quality-manifest.json", regen: "groundtruth audit --root examples/minijudge --name minijudge"}
  - {path: "examples/minijudge/runs/assurance-report.md", regen: "groundtruth audit --root examples/minijudge --name minijudge"}
  - {path: "examples/minijudge/runs/agreement.json", regen: "cd examples/minijudge && python scripts/judge.py"}
  - {path: "runs/steward/repo-manifest.json", regen: "groundtruth steward"}
  - {path: "runs/steward/steward-report.md", regen: "groundtruth steward"}
frozen:
  - {path: "examples/minijudge", commit: "3d294a37356f3e31c3940d5c2078c49039545b27"}
layer_rules:
  - {kind: forbid, src: "groundtruth.core", dst: "groundtruth.products"}
  - {kind: forbid, src: "groundtruth.core", dst: "groundtruth.meta"}
  - {kind: forbid, src: "groundtruth.core", dst: "groundtruth.steward"}
  - {kind: forbid, src: "groundtruth.meta", dst: "groundtruth.core"}
  - {kind: forbid, src: "groundtruth.meta", dst: "groundtruth.products"}
  - {kind: forbid, src: "groundtruth.meta", dst: "groundtruth.adapters"}
  - {kind: forbid, src: "groundtruth.meta", dst: "groundtruth.steward"}
  - {kind: stdlib_only, src: "groundtruth.steward"}
  - {kind: only_importer, dst: "groundtruth.steward", allowed: ["groundtruth.cli"]}
exemptions: []
```
