# Contributing to Groundtruth

Groundtruth is a research artifact as much as a codebase: every published
number is measured, every claim lives in a register, and the repository
audits itself in CI. Contributions are welcome inside those rules — the
rules are the project.

**Status.** Groundtruth shipped v0.8.0 and is in v1 stabilization.
Engineering is frozen: no new features or architecture changes are being
accepted; bug fixes are accepted when they invalidate a published claim.
The most valuable contribution right now is an **external reproduction
report** (see below) — it discharges the project's stated single-author
independence limit (threat E6 in [docs/threats.yaml](docs/threats.yaml)).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q          # 170 tests, ~12 s, no network needed
```

Optional: a local [Ollama](https://ollama.com) server for real-model
subjects (`groundtruth run --agent ollama:<model>`). Everything else is
offline and deterministic.

## The repository polices itself

Before anything is merged, the same gates that run in CI must pass
locally — this is Constitution Law 13, a checklist of existing commands:

```bash
pytest -q                                                    # tests green
groundtruth audit                                            # rc 0
groundtruth audit --root examples/minijudge --name minijudge # rc 0
groundtruth steward                                          # rc 0
```

Two things trip newcomers:

1. **Every tracked file needs a role.** The role rules in
   [docs/CONSTITUTION.md](docs/CONSTITUTION.md) are catch-none: a file no
   rule matches is a finding, not a default (Law 2). Adding a new
   top-level file means amending the declarations block *in the same
   commit*, with the justification in the commit message (the amendment
   rule at the top of the Constitution).
2. **Derived artifacts are committed and diffed.** Anything under a
   declared `derived_artifacts` entry must be regenerated and committed
   together with the change that affects it, until `git diff` over those
   paths is clean — CI regenerates and diffs them, so a stale committed
   artifact fails the build (Law 5).

## Making a change

- Conventional commit messages (`feat:`, `fix:`, `docs:`, `ci:`,
  `test:`), with the engineering intent in the body.
- Behavior changes come with tests. Detector changes deliberately force
  the published quality numbers to be updated: they are pinned by a
  regression test, so the numbers cannot drift silently.
- No claim without in-repo evidence. If a change adds a claim, it goes in
  [docs/claims.yaml](docs/claims.yaml) with its evidence path and threat
  references — `groundtruth audit` checks both directions.
- New scenarios are YAML files under `scenarios/agentprobe/` — the schema
  is in the README ("Add a scenario"). Discriminating scenarios (ones
  some models pass and some fail) are worth more than another universal
  failure.

## Reproduction reports — the most valuable contribution

Clone the repository fresh and follow the README quickstart verbatim.
Expected: 170 tests green; the demo frontier scores 0.25 / 1.00 / 0.75;
`groundtruth steward` and both audits exit 0 with artifacts byte-identical
to the committed copies. Then open an issue with the **reproduction
report** template — whether it worked or not. A failed or frictious
reproduction is a finding, not noise; the project's own external
validation phase was built on exactly this procedure.

## Questions

Open an issue. For suspected security problems, see
[SECURITY.md](SECURITY.md).
