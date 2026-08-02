"""`groundtruth rescore` — re-score committed traces without a live model.

The property that matters is faithfulness: re-evaluating the committed traces
with the suite's current detector set must reproduce the committed scorecards
byte-for-byte. That is what makes a detector change propagable and what lets CI
check `runs/` for staleness (finding R4).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from groundtruth.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS = REPO_ROOT / "runs"
TRACES = RUNS / "traces"


def _slugs() -> list[str]:
    return sorted(p.name for p in TRACES.iterdir() if p.is_dir())


def test_rescore_check_reproduces_every_committed_scorecard(capsys):
    """The gate: with the current detectors, every committed scorecard is
    exactly what re-scoring the committed traces produces."""
    rc = main(["rescore", "--check"])

    out = capsys.readouterr().out
    assert rc == 0, out
    assert f"{len(_slugs())} scorecard" in out
    assert "identical" in out


def test_rescore_check_writes_nothing(tmp_path):
    """--check is what CI calls: it must never mutate the artifacts it audits."""
    runs = tmp_path / "runs"
    runs.mkdir()
    for card in RUNS.glob("scorecard-*.json"):
        shutil.copy2(card, runs / card.name)
    before = {p.name: p.read_bytes() for p in runs.glob("*.json")}

    rc = main(["rescore", "--check", "--traces", str(TRACES), "--runs", str(runs)])

    assert rc == 0
    assert {p.name: p.read_bytes() for p in runs.glob("*.json")} == before


def test_rescore_writes_bytes_identical_to_the_committed_scorecard(tmp_path):
    """Same serialization as `run --out`: a rescore must not churn the diff."""
    slug = "mistral-7b"

    rc = main(["rescore", "--subject", slug, "--traces", str(TRACES), "--runs", str(tmp_path)])

    assert rc == 0
    written = (tmp_path / f"scorecard-{slug}.json").read_bytes()
    assert written == (RUNS / f"scorecard-{slug}.json").read_bytes()


def test_rescore_check_fails_loudly_on_a_stale_scorecard(tmp_path, capsys):
    runs = tmp_path / "runs"
    runs.mkdir()
    for card in RUNS.glob("scorecard-*.json"):
        shutil.copy2(card, runs / card.name)
    stale = runs / "scorecard-mistral-7b.json"
    card = json.loads(stale.read_text())
    card["robustness_score"] = 0.99
    stale.write_text(json.dumps(card, indent=2))

    rc = main(["rescore", "--check", "--traces", str(TRACES), "--runs", str(runs)])

    out = capsys.readouterr().out
    assert rc == 1
    assert "mistral-7b" in out
    assert "robustness_score" in out


def test_rescore_names_the_subject_when_traces_are_missing(tmp_path, capsys):
    rc = main(["rescore", "--subject", "no-such-model", "--traces", str(TRACES),
               "--runs", str(tmp_path)])

    assert rc == 2
    err = capsys.readouterr().err
    assert "no-such-model" in err
    assert "mistral-7b" in err  # the message lists what *is* available


def test_rescore_reports_a_missing_case_against_the_scenario_list(tmp_path, capsys):
    """A trace directory that does not cover the suite is an error, not a
    silently smaller scorecard."""
    traces = tmp_path / "traces" / "partial"
    traces.mkdir(parents=True)
    src = TRACES / "mistral-7b"
    shutil.copy2(src / "trace-benign_control_05.json", traces / "trace-benign_control_05.json")

    rc = main(["rescore", "--subject", "partial", "--traces", str(tmp_path / "traces"),
               "--runs", str(tmp_path)])

    assert rc == 2
    assert "benign_completion_08" in capsys.readouterr().err
