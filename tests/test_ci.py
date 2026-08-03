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


def test_ci_fails_closed_on_unexplained_improvement(tmp_path, capsys):
    """Finding D4. The gate used to print "improvement — consider refreshing"
    and return 0, so a detector that regressed and stopped firing raised
    robustness and PASSED the safety gate. It also left the baseline stale,
    which under-constrains the next comparison: a later slide back part-way
    would then read as "no regression".

    An improvement is therefore a finding, not a pleasantry. The two legal
    exits are the ones the Constitution already names — refresh the baseline
    with `--update` in the commit that earned the improvement, or investigate
    the detector that stopped firing. Neither is "carry on"."""
    baseline = tmp_path / "baseline.json"
    main(["ci", "--agent", "vulnerable_agent", "--baseline", str(baseline), "--update"])

    rc = main(["ci", "--agent", "hardened_agent", "--baseline", str(baseline)])

    out = capsys.readouterr().out.lower()
    assert rc == 1
    assert "unexplained improvement" in out
    assert "--update" in out


def test_ci_names_the_cases_that_stopped_failing(tmp_path, capsys):
    """An improvement is only actionable if you can see which cases moved —
    that is what tells a real fix apart from a detector that went quiet."""
    baseline = tmp_path / "baseline.json"
    main(["ci", "--agent", "vulnerable_agent", "--baseline", str(baseline), "--update"])

    main(["ci", "--agent", "hardened_agent", "--baseline", str(baseline)])

    assert "indirect_injection_01" in capsys.readouterr().out


def test_ci_still_passes_when_nothing_moved(tmp_path, capsys):
    """Fail-closed must not mean fail-always: an unchanged subject against its
    own baseline is the case CI runs on every push, and it stays green."""
    baseline = tmp_path / "baseline.json"
    main(["ci", "--agent", "hardened_agent", "--baseline", str(baseline), "--update"])

    rc = main(["ci", "--agent", "hardened_agent", "--baseline", str(baseline)])

    assert rc == 0
    assert "no regression" in capsys.readouterr().out.lower()
