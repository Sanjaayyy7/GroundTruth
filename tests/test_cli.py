"""CLI contract: `groundtruth validate` reports measured detector quality."""
from __future__ import annotations

import json

from groundtruth.cli import main


def test_validate_emits_json_report(capsys):
    rc = main(["validate", "--suite", "agentprobe", "--json"])

    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["n_items"] >= 50
    assert report["micro"]["precision"] is not None
    assert "secret_exfiltration" in report["per_category"]


def test_validate_writes_report_file(tmp_path, capsys):
    out = tmp_path / "quality.json"

    rc = main(["validate", "--suite", "agentprobe", "--out", str(out)])

    assert rc == 0
    assert json.loads(out.read_text())["n_items"] >= 50


def test_validate_human_output_names_the_misses(capsys):
    main(["validate", "--suite", "agentprobe"])

    text = capsys.readouterr().out
    assert "precision" in text
    assert "ut_pos_04_semantic_gap" in text  # misses are shown, not hidden


def test_cli_is_cwd_independent(tmp_path, monkeypatch, capsys):
    """Suite data resolves against the repo, not the caller's directory —
    required for CI checkouts and any install used outside the repo root."""
    monkeypatch.chdir(tmp_path)

    rc = main(["run", "--agent", "hardened_agent", "--json"])

    assert rc == 0
    assert json.loads(capsys.readouterr().out)["robustness_score"] == 1.0


def test_scorecard_json_carries_schema_version(capsys):
    main(["run", "--agent", "hardened_agent", "--json"])

    assert json.loads(capsys.readouterr().out)["schema_version"] == 1
