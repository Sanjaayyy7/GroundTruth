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


def test_stateful_flag_builds_history_carrying_ollama_subject():
    """--stateful is the benchmark's second measurement condition (v0.4):
    the subject must be distinguishable so stateful scorecards can never be
    confused with published stateless ones."""
    from groundtruth.cli import _resolve_agent

    agent = _resolve_agent("ollama:m", stateful=True)
    assert agent.name == "ollama:m+stateful"
    assert _resolve_agent("ollama:m").name == "ollama:m"


def test_stateful_flag_rejects_scripted_agents(capsys):
    """Scripted demo subjects have no context window; silently ignoring the
    flag would fabricate a measurement condition that never existed."""
    rc = main(["run", "--agent", "vulnerable_agent", "--stateful", "--json"])

    assert rc == 2
    assert "stateful" in capsys.readouterr().err.lower()


# --- audit ------------------------------------------------------------------

def _write_green_evaluation(root):
    """A minimal on-disk evaluation whose audit passes every contract."""
    import subprocess

    (root / "docs").mkdir()
    (root / "data").mkdir()
    (root / "scripts").mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "--allow-empty", "-m", "x"], cwd=root, check=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                         capture_output=True, text=True, check=True).stdout.strip()
    (root / "docs/claims.yaml").write_text(f"""\
schema_version: 2
harness_commit: {sha}
claims:
  - id: C1
    statement: "example claim"
    classification: fact
    evidence:
      - data/real.txt
    reproduce: "python scripts/run.py"
    falsification: "counterexample"
    confidence: high
    scope: "fixture"
    threat_refs: [T1]
""")
    (root / "docs/threats.yaml").write_text("""\
schema_version: 1
threats:
  - id: T1
    category: internal
    threat: "example threat"
    mitigation: "documented"
    remaining_risk: "some"
    future_experiment: "run more"
    status: mitigated
    claim_refs: [C1]
""")
    (root / "docs/THREATS_TO_VALIDITY.md").write_text("| T1 | x |\n")
    (root / "data/real.txt").write_text("evidence")
    (root / "scripts/run.py").write_text("pass")
    (root / "pyproject.toml").write_text('[project]\nversion = "0.6.0"\n')
    (root / "README.md").write_text("| X | y | **v0.6 — shipping** |\n")


def test_audit_green_on_fixture(tmp_path, capsys):
    _write_green_evaluation(tmp_path)

    rc = main(["audit", "--root", str(tmp_path),
               "--out", str(tmp_path / "m.json"), "--report", str(tmp_path / "a.md")])

    assert rc == 0
    assert (tmp_path / "m.json").exists() and (tmp_path / "a.md").exists()
    assert "all contracts hold" in capsys.readouterr().out


def test_audit_finding_returns_1(tmp_path):
    _write_green_evaluation(tmp_path)
    (tmp_path / "data/real.txt").unlink()  # break CT1

    rc = main(["audit", "--root", str(tmp_path),
               "--out", str(tmp_path / "m.json"), "--report", str(tmp_path / "a.md")])

    assert rc == 1


def test_audit_malformed_register_returns_2(tmp_path, capsys):
    _write_green_evaluation(tmp_path)
    (tmp_path / "docs/claims.yaml").write_text("claims: 3\n")

    rc = main(["audit", "--root", str(tmp_path)])

    assert rc == 2
    assert "claims.yaml" in capsys.readouterr().err
