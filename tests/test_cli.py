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


def test_validate_with_judge_swaps_the_detector_set(monkeypatch, capsys):
    """--judge measures an LLM judge on the same labeled set with the same
    machinery — the rules-vs-judge comparison instrument. Stubbed here; the
    judge's own parsing contract lives in test_judge.py."""
    import groundtruth.cli as cli

    class StubJudge:
        def __init__(self, model):
            self.name = f"llm_judge:{model}"

        def detect(self, case, trace):
            return []

    monkeypatch.setattr(cli, "LLMJudge", StubJudge)

    rc = cli.main(["validate", "--judge", "stub-model", "--json"])

    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["micro"]["tp"] == 0  # silent judge = pure recall loss, honestly counted
    assert report["micro"]["fn"] > 30


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


def test_run_persists_traces_when_asked(tmp_path, capsys):
    """--traces-out writes every raw trace — the substrate for labeling real
    (non-designed) model behavior into the validation set."""
    rc = main(["run", "--agent", "vulnerable_agent", "--json", "--traces-out", str(tmp_path)])

    assert rc == 0
    files = sorted(tmp_path.glob("trace-*.json"))
    assert len(files) == 8  # one per scenario
    trace = json.loads(files[0].read_text())
    assert trace["schema_version"] == 1
    assert trace["subject"] == "vulnerable_agent"
    assert trace["spans"]
