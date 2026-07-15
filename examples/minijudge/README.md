# MiniJudge — **v0.1 — shipping**

A deliberately minimal judge-agreement evaluation: a negation-keyword judge
predicts `support`/`refute` verdicts for 12 factual statements and is
measured against reference verdicts (`runs/agreement.json`, accuracy 0.75).

## Why this exists

MiniJudge is the **second consumer** for Groundtruth's Meta-Evaluation
Engine (v0.7 external validation). It exists to answer one question: can
`groundtruth audit` audit an evaluation Groundtruth did not produce, using
only the published register formats? It is not JudgeKit, it is not a
product, and it must not grow.

It differs from Groundtruth wherever reasonable — domain (judge agreement,
not agent red-teaming), terminology (verdicts/agreement, not
scorecards/robustness), data format (JSON, not YAML scenarios), threat-ID
family (`T…`, exercising the loader grammar branch Groundtruth never uses) —
while emitting the same register formats: `docs/claims.yaml` (schema v2),
`docs/threats.yaml` (schema v1), `docs/THREATS_TO_VALIDITY.md`, and the
version anchors this README and `pyproject.toml` provide.

## Run it

```bash
python scripts/judge.py                      # regenerate runs/agreement.json
groundtruth audit --root examples/minijudge --name minijudge   # from the repo root
```

The audit constructs the evidence graph from MiniJudge's registers, checks
every contract (CT1–CT9), and writes `runs/quality-manifest.json` and
`runs/assurance-report.md` here. Negative controls live in
`tests/test_external_validation.py`.
