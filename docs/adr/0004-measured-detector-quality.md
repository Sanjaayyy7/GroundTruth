# ADR-0004: Detector quality is measured, not asserted

**Status:** accepted · **Date:** 2026-07-12

## Context
Every eval tool ships detectors/metrics; almost none measures the quality of
its own detectors. Unmeasured detectors are unfalsifiable opinions.

## Decision
A platform Validation Engine (`core/validation.py`) measures every detector
against a hand-labeled trace set (`validation/agentprobe/`, 53 items) that
deliberately includes hard cases the current rules are *expected* to get
wrong. `groundtruth validate` reports per-category precision/recall and
names every miss. A snapshot test pins the measured numbers so a detector
change forces the published numbers to change with it.

## Methodology limits (stated, not hidden)
Labels are single-annotator (the developer). Hard cases are designed, not
sampled from the wild. The numbers measure rule coverage on this set — they
are not claims about attack-space coverage.

## Rejected
- *Tuning detectors until the set reads 100%*: converts measurement into
  theater; the misses are the documentation of rule limits.
- *Skipping labels until third-party annotators exist*: perfect blocking good.

## Review trigger
First external contributor: add inter-rater agreement on a label subset.
