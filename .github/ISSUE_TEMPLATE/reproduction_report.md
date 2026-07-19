---
name: Reproduction report
about: Results of a clean-clone reproduction — successes and failures are equally valuable
title: "Reproduction report: "
labels: reproduction
---

Thank you — external reproduction is the single most valuable contribution
to this project (it discharges the stated single-author limit, threat E6).
Please follow the README quickstart verbatim from a fresh clone and report
what actually happened, including friction.

**Environment:**

- OS / architecture:
- Python version:
- Date / commit reproduced (`git rev-parse --short HEAD`):

**Results** (fill in what you observed, not what was expected):

| Check | Expected | Observed |
|---|---|---|
| `pytest -q` | 170 passed | |
| `groundtruth run --agent vulnerable_agent` | robustness 0.25 | |
| `groundtruth run --agent hardened_agent` | robustness 1.00 | |
| `groundtruth run --agent paranoid_agent` | robustness 0.75 | |
| `groundtruth steward` exit code | 0 | |
| `groundtruth audit` exit code | 0 | |
| `git status` after audits/steward | clean (artifacts byte-identical) | |

**Undocumented steps needed** (anything you had to figure out that the
README did not say):

**Friction / confusion** (anything that slowed you down, even if it
worked):
