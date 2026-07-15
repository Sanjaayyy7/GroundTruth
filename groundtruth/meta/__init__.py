"""Meta-evaluation engine: constructs an auditable evidence model from
evaluation artifacts and derives reproducible assessments from that model.

Current consumers: `groundtruth audit` CLI.
Future consumers (named, not built): JudgeKit registers, PlannerBench
registers, external evaluations emitting the same register formats.
"""
