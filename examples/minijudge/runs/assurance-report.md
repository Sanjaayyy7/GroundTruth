# Assurance Report

Evaluation evidence @ `074bfb3`.

## Strongly supported

- **claim:J1** The negation-keyword judge agrees with the reference verdicts on 9 of 12 items (accuracy 0.75) on la…
  - evidence: `data/labeled.json`
  - evidence: `runs/agreement.json`
  - reproduce: `python scripts/judge.py`

## Provisional

- **claim:J2** (supported_observation) All three judge errors are negation-driven: two true statements that contain negation are predicted …
  - blocking: judge and labeled set share an author; the error pattern may be a dataset artifact

## Retracted — kept on the record

- None.

## Unresolved threats

### construct
- **threat:T3** Negation keywords are a proxy for semantic refutation
  - next: Add a negation-aware baseline and compare error classes

### statistical
- **threat:T1** 12 items cannot support generalization beyond this labeled set
  - next: Grow the labeled set past 50 items before quoting accuracy without this caveat.
- **threat:T2** Reference verdicts and judge share one author
  - next: Independent second annotator over all 12 items

## Contract findings

All contracts hold.

## Labeling needs

- **threat:T2** annotators: 1, kappa: blocked_on_second_annotator

No aggregate verdict: assurance is reported per conclusion, not per repository.
