# ADR-0007: Second-consumer validation — what MiniJudge proved and changed

**Status:** accepted · **Date:** 2026-07-15

## Context

ADR-0006 shipped the Meta-Evaluation Engine with a reuse claim ("future
consumers: JudgeKit, PlannerBench, external evaluations emitting the same
register formats") and a named generalization trigger. v0.7 tested that
claim experimentally, under a pre-registered protocol
(`docs/specs/2026-07-15-v07-external-validation-protocol.md`): MiniJudge, a
minimal real judge-agreement evaluation authored to the published register
formats, audited by the unmodified engine, with negative controls.

## Decision

1. **The engine's reuse surface is confirmed to be the register formats,
   not Python interfaces.** MiniJudge passed with zero changes to
   `groundtruth/meta/` (diff vs the protocol commit: empty). The one
   adaptation was CLI-surface only: `audit --name` exposes the
   `evaluation_name` parameter `build_manifest` always had. Four-question
   justification: (evidence) the second consumer's manifest self-identified
   as "groundtruth"; (why v0.6 lacked it) with one consumer the default was
   always correct; (why a second consumer requires it) a manifest that
   misnames its evaluation fails its own purpose; (why future consumers
   inherit it) every consumer has a name.
2. **Implicit conventions are now explicit format law**, documented rather
   than generalized away:
   - the prose threat doc lives at `docs/THREATS_TO_VALIDITY.md` under the
     evaluation root (loader + CT8 assume it);
   - threat IDs match `[IEKS]\d+ | T\d+` (MiniJudge deliberately exercised
     the `T\d+` branch Groundtruth never used);
   - version anchors are `pyproject.toml` `version = "…"` and a README
     line matching `**vX.Y — shipping**` (CT6);
   - `harness_commit` must exist in the git history reachable from the
     evaluation root;
   - reproduce-command path checking skips `./.venv`-prefixed tokens.
   Each is a documented requirement a consumer can satisfy; none needed a
   code change. A consumer that *cannot* satisfy one (e.g. a non-Python
   evaluation with no pyproject.toml) is the named trigger for revisiting
   the corresponding assumption — with evidence, not in advance.
3. **The generalization trigger has NOT fully fired.** ADR-0006 names
   JudgeKit's registers as the trigger for loader generalization and Core
   admission review. MiniJudge is deliberately minimal, same-author,
   same-repo (threat E6). No abstract base classes, plugin systems,
   registries, or extension APIs were introduced; `meta/` stays outside
   Core. The ≥2-realized-consumer bar for *Core admission* is arguably met
   in the narrow sense (two audited register sets), but the spirit —
   independent product pressure shaping the abstraction — is not; Core
   admission waits for JudgeKit proper.
4. **"Evaluation assurance platform" is still not an earned phrase.**
   v0.7 upgrades the honest description from "an agent-evaluation
   framework that audits its own evidence" to "…and has demonstrated that
   audit on a second evaluation's registers." Organizational independence
   (an externally authored consumer, no coordination beyond format docs)
   is E6's future experiment and the remaining gate on the platform framing.

## Rejected

- *Generalizing the loader now* (second register family, pluggable prose
  paths, configurable ID grammars): one same-author consumer is evidence of
  format adequacy, not of variation the engine must absorb.
- *Growing MiniJudge into JudgeKit*: MiniJudge's value is that it is small
  enough to be obviously not the point; JudgeKit deserves its own design
  under its own milestone.
- *A consumer-conformance test-kit / spec suite*: premature at n=2 with
  shared authorship; reconsider when an external consumer first tries to
  emit the formats.

## Consequences

The reuse claim in ADR-0006 is now experimental fact (claim C11,
preregistered 074bfb3 → 3d294a3), scoped by E6. CI audits two evaluations
on every push, so a change to the engine or the formats that breaks either
consumer fails the build. Cost: the format conventions in Decision 2 are
now load-bearing for outsiders and must be kept documented; a breaking
format change requires migrating two register sets.

## Review trigger

Unchanged from ADR-0006: JudgeKit's real registers. Additionally: the first
externally authored evaluation attempting the formats (E6's experiment)
reopens Decisions 2–4.
