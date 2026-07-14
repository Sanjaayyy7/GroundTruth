# Groundtruth — Reproducibility Guide

Goal: **a stranger clones the repo and reproduces every published number without
author intervention.** Every command below was run from a fresh virtualenv
during the v0.5 audit; the determinism results are measured, not asserted.

## Environment

- Python **3.11+** (`requires-python = ">=3.11"`).
- Runtime dependency: **PyYAML** only. Dev extra: **pytest**.
- For the LLM-subject numbers: a local **Ollama** server on `:11434` with the
  six models pulled (`gemma3:4b`, `llama3.1:8b`, `llama3.2:latest`, `qwen3:4b`,
  `phi4-mini`, `mistral:7b`). No API keys, no GPU required, $0.
- The rule/detector numbers and the full test suite need **no model at all**.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Expected: clean install, no build step (pure Python).

## Tier 1 — no model needed (deterministic, guaranteed)

```bash
pytest -q
```
Expected: **78 passed** in ~7 s. Verified from a fresh venv during the v0.5 audit.

```bash
groundtruth validate --out runs/detector-quality.json
```
Expected micro: **P 0.9333 · R 0.8936 · F1 0.9130 · tp 42 / fp 3 / fn 5**, with
`non_completion` at 10/0/0. The named misses (`ut_pos_04_semantic_gap`,
`ih_pos_04_offtarget`, `sl_pos_04_split`, …) print every run — they are the
documentation of rule limits, not regressions.

```bash
python experiments/detector_quality_ci.py
```
Expected: bootstrap 95% CI (10k resamples, seed 42) **precision [0.8448, 1.0000],
recall [0.7895, 0.9778]**. Deterministic across runs (seeded).

```bash
groundtruth run --agent vulnerable_agent --json --out /tmp/a.json
groundtruth run --agent vulnerable_agent --json --out /tmp/b.json
diff /tmp/a.json /tmp/b.json     # -> no output: BYTE-IDENTICAL
```
Expected: `vulnerable_agent` robustness **0.25**, `hardened_agent` **1.0**,
`paranoid_agent` **0.75**. Diff is empty — scripted subjects are deterministic
by construction.

## Tier 2 — local Ollama needed (deterministic in practice, measured)

```bash
groundtruth run --agent ollama:llama3.2:latest --json --out /tmp/s.json
diff runs/scorecard-llama3.2-latest.json /tmp/s.json   # -> BYTE-IDENTICAL (measured)

groundtruth run --agent ollama:llama3.2:latest --stateful --json --out /tmp/sf.json
diff runs/scorecard-llama3.2-latest-stateful.json /tmp/sf.json  # -> BYTE-IDENTICAL (measured)
```
During the v0.5 audit both diffs were empty **from a fresh virtualenv**.
Byte-identity is empirical: it holds while the local Ollama build and model
weights are unchanged (see C9 / threat I5). Other five models reproduce
equal *scores*; byte-diffing all six is a listed future check.

Full re-benchmark (both conditions, six models): ~15 min wall clock, dominated
by qwen3 (thinking, 314–446 s). Per-model stateless/stateful times are recorded
in the SPEC and the re-bench log.

## Tier 3 — the flagship experiment

```bash
python experiments/stall_confounds/run.py
```
Expected: **~295 s**, 55 runs, writes `runs/experiments/stall-confounds-<date>/`.
The verdict — 9/9 stalls persist at every stateless budget, 0/9 survive state —
is reproduced against the pre-registered predictions in
`experiments/stall_confounds/PREDICTIONS.md` (committed *before* the run, at
`040c804`; verify with `git log`).

## Determinism guarantees (precise)

| Layer | Guarantee | Basis |
|---|---|---|
| Core, detectors, validation | Byte-identical, always | Pure functions, no clock/RNG/network |
| Scripted demo subjects | Byte-identical, always | Deterministic by construction |
| Ollama subjects | Byte-identical in practice | temp 0 + seed 42; measured for llama3.2 both conditions |
| Wall-clock times | Not reproducible | Hardware-dependent; never a published claim |

## Acceptable variance

- LLM wall-clock: any (hardware/thermal). Never asserted.
- LLM scorecard *content*: expected zero drift at temp 0 / seed 42; a differing
  scorecard is a finding (record it, do not average it away).
- Bootstrap CI: zero drift (seeded).

## Common failure modes

- `No module named pytest` → install the dev extra: `pip install -e ".[dev]"`.
- Tier-2/3 skipped or erroring → Ollama server not running, or a model not
  pulled; the live pytest test auto-skips when `:11434` is unreachable.
- A shell that parses `.[dev]` as a glob (zsh) → quote it: `pip install -e ".[dev]"`.

## Verification checklist

- [ ] Fresh venv, `pip install -e ".[dev]"` succeeds
- [ ] `pytest -q` → 78 passed
- [ ] `groundtruth validate` → micro 0.9333 / 0.8936
- [ ] CI script → CI [0.8448,1.0000] / [0.7895,0.9778]
- [ ] `vulnerable_agent` double-run diff is empty
- [ ] (Ollama) llama3.2 stateless + stateful diffs against committed scorecards are empty
- [ ] (Ollama) `stall_confounds/run.py` verdict matches REPORT.md against pre-registered predictions
