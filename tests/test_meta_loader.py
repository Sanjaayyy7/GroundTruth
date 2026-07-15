"""Evidence Loader — the one concrete adapter (YAML/filesystem/git -> model)."""
from pathlib import Path

import pytest

from groundtruth.meta.loader import RegisterError, load_evidence

CLAIMS_MIN = """\
schema_version: 2
harness_commit: abc1234
claims:
  - id: C1
    statement: "example claim"
    classification: fact
    evidence:
      - data/real.txt
      - external: "outside log"
        why: "kept off-repo"
    reproduce: "python scripts/run.py --fast"
    falsification: "counterexample"
    confidence: high
    scope: "fixture"
    threat_refs: [T1]
    metrics:
      - {name: p, value: 0.5, source: data/metrics.json, path: micro.p}
"""

THREATS_MIN = """\
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
"""


@pytest.fixture()
def fixture_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "docs/claims.yaml").write_text(CLAIMS_MIN)
    (tmp_path / "docs/threats.yaml").write_text(THREATS_MIN)
    (tmp_path / "docs/THREATS_TO_VALIDITY.md").write_text("| T1 | x |\n")
    (tmp_path / "data/real.txt").write_text("evidence")
    (tmp_path / "data/metrics.json").write_text('{"micro": {"p": 0.5}}')
    (tmp_path / "scripts/run.py").write_text("pass")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.6.0"\n')
    (tmp_path / "README.md").write_text("| X | y | **v0.6 — shipping** |\n")
    return tmp_path


GIT_FACTS = {"abc1234": {"exists": True}, "__ancestry__": {}}


def _by_id(nodes):
    return {n.id: n for n in nodes}


def test_loads_nodes_with_resolved_environment(fixture_repo):
    nodes = _by_id(load_evidence(fixture_repo, git_facts=GIT_FACTS))
    assert nodes["claim:C1"].attrs["classification"] == "fact"
    assert nodes["artifact:data/real.txt"].attrs["exists"] is True
    assert nodes["claim:C1"].attrs["external_evidence"][0]["why"] == "kept off-repo"
    assert nodes["experiment:C1"].attrs["script_paths"] == {"scripts/run.py": True}
    assert nodes["claim:C1"].attrs["metrics_resolved"][0]["actual"] == 0.5
    v = nodes["version:abc1234"]
    assert v.attrs == {
        "exists_in_git": True, "pyproject_version": "0.6.0", "readme_version": "0.6",
    }
    assert nodes["threat:T1"].attrs["status"] == "mitigated"
    assert nodes["artifact:docs/THREATS_TO_VALIDITY.md"].attrs["prose_threat_ids"] == ["T1"]


def test_missing_evidence_file_is_recorded_not_raised(fixture_repo):
    (fixture_repo / "data/real.txt").unlink()
    nodes = _by_id(load_evidence(fixture_repo, git_facts=GIT_FACTS))
    assert nodes["artifact:data/real.txt"].attrs["exists"] is False


def test_glob_evidence_counts_matches(fixture_repo):
    claims = (fixture_repo / "docs/claims.yaml").read_text().replace(
        "- data/real.txt", "- data/*.txt")
    (fixture_repo / "docs/claims.yaml").write_text(claims)
    nodes = _by_id(load_evidence(fixture_repo, git_facts=GIT_FACTS))
    assert nodes["artifact:data/*.txt"].attrs == {"exists": True, "glob": True, "matches": 1}


def test_malformed_register_raises_register_error(fixture_repo):
    (fixture_repo / "docs/claims.yaml").write_text("claims: 3\n")
    with pytest.raises(RegisterError, match="claims.yaml"):
        load_evidence(fixture_repo, git_facts=GIT_FACTS)


def test_missing_register_raises_register_error(fixture_repo):
    (fixture_repo / "docs/threats.yaml").unlink()
    with pytest.raises(RegisterError, match="threats.yaml"):
        load_evidence(fixture_repo, git_facts=GIT_FACTS)
