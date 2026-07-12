# Groundtruth — Positioning & Philosophy

## One sentence

Groundtruth is the offline reliability gate for AI systems: deterministic
red-team evaluation whose detectors are themselves measured.

## One paragraph

Before an AI system ships, something has to answer "when does this fail, and
why?" — offline, reproducibly, and honestly. Groundtruth is that layer. It runs
subjects (agents today; judges and planners next) through adversarial and
benign scenarios with deterministic mocked tools, records every step as a
trace, and emits structured, explanatory failures — category, severity, causal
chain, fix — never a bare score. Uniquely, it applies the same discipline to
itself: every detector's precision and recall is measured against a
hand-labeled trace set whose known misses are published, not hidden. If the
number isn't measured, Groundtruth doesn't print it.

## Philosophy

1. **Explain failure, don't count it.** The atomic unit is an explanatory
   Failure, not a metric.
2. **Determinism is the product.** A reliability claim that can't be re-run
   byte-identically is an anecdote.
3. **Measure the measuring stick.** Detectors have published precision/recall
   and named misses. Unmeasured detectors are opinions.
4. **The utility side counts.** An agent that refuses everything is not safe,
   it is useless — `over_refusal` is a first-class failure.
5. **Abstractions earn their place.** Nothing enters the core without two
   named product consumers (ADR-0001).
6. **Honesty over impressiveness.** Limits are stated where the numbers are
   stated. Single-annotator labels are disclosed as such.

## Position against the ecosystem

| They optimize for | Groundtruth's stance |
|---|---|
| OpenTelemetry: neutral trace standard | borrow trace-shape compatibility; reject committee genericity |
| Langfuse / Phoenix: online production observability | stay offline & pre-ship; different layer, not a competitor |
| DeepEval: breadth of pytest-style metrics | reject metric breadth; they don't measure their own metrics — we do |
| Promptfoo: config-driven prompt testing in CI | borrow CI-first distribution; operate at trace/agent level, not prompt level |
| Inspect AI: rigorous general eval framework | closest relative; differentiate by being opinionated about agent reliability + self-measured detectors |
| MLflow / W&B: experiment tracking UX | borrow artifact/registry ideas; never compete on UI |

## What Groundtruth will not build (permanent anti-goals)

- A general-purpose LLM metrics library.
- A production observability dashboard.
- Online/live tracing.
- Abstractions with fewer than two consumers.
- Any published number without an auditable methodology behind it.
- A leaderboard without a published methodology and reproduction path.
- A framework before a product: no primitive ships ahead of the product
  that needs it.
- Manifesto-first development: strategy is reviewed once per version gate,
  then the version ships. Evidence, not essays, moves the roadmap.
