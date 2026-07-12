"""Contract for `groundtruth ci` — the regression gate.

The gate compares a fresh scorecard against a stored baseline and fails the
build when safety regresses. Deterministic demo agents make these tests exact:
same agent twice can never regress; swapping in a worse agent must fail with
the newly-failing cases named.
"""
from __future__ import annotations

import json

from groundtruth.cli import main


def test_ci_update_creates_baseline(tmp_path, capsys):
    baseline = tmp_path / "baseline.json"

    rc = main(["ci", "--agent", "hardened_agent", "--baseline", str(baseline), "--update"])

    assert rc == 0
    d = json.loads(baseline.read_text())
    assert d["robustness_score"] == 1.0
    assert d["schema_version"] == 1


def test_ci_errors_when_baseline_missing(tmp_path, capsys):
    rc = main(["ci", "--agent", "hardened_agent", "--baseline", str(tmp_path / "none.json")])

    assert rc == 2
    assert "baseline" in capsys.readouterr().err.lower()


def test_ci_passes_when_no_regression(tmp_path, capsys):
    baseline = tmp_path / "baseline.json"
    main(["ci", "--agent", "vulnerable_agent", "--baseline", str(baseline), "--update"])

    rc = main(["ci", "--agent", "vulnerable_agent", "--baseline", str(baseline)])

    assert rc == 0
    assert "no regression" in capsys.readouterr().out.lower()


def test_ci_fails_on_regression_and_names_new_failures(tmp_path, capsys):
    baseline = tmp_path / "baseline.json"
    main(["ci", "--agent", "hardened_agent", "--baseline", str(baseline), "--update"])

    # a worse subject against the clean baseline = a safety regression
    rc = main(["ci", "--agent", "vulnerable_agent", "--baseline", str(baseline)])

    assert rc == 1
    out = capsys.readouterr().out
    assert "regression" in out.lower()
    assert "indirect_injection_01" in out  # newly failing cases are named, not counted


def test_ci_reports_improvement_without_failing(tmp_path, capsys):
    baseline = tmp_path / "baseline.json"
    main(["ci", "--agent", "vulnerable_agent", "--baseline", str(baseline), "--update"])

    rc = main(["ci", "--agent", "hardened_agent", "--baseline", str(baseline)])

    assert rc == 0
    assert "improve" in capsys.readouterr().out.lower()
