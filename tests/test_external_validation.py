"""v0.7 external validation: the Meta-Evaluation Engine audits an evaluation
it did not produce (examples/minijudge), with zero modification to meta/.

Protocol: docs/specs/2026-07-15-v07-external-validation-protocol.md.
Success criteria 1-6 map onto the tests below; the negative controls prove
the green audit is not vacuous.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from groundtruth.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]
MINIJUDGE = REPO_ROOT / "examples/minijudge"


def _audit(root: Path, tmp_path: Path, name: str = "minijudge") -> int:
    return main([
        "audit", "--root", str(root), "--name", name,
        "--out", str(tmp_path / "manifest.json"),
        "--report", str(tmp_path / "assurance.md"),
    ])


@pytest.fixture()
def minijudge_copy(tmp_path):
    """MiniJudge copied to a scratch git repo, harness_commit rewritten to a
    commit that exists there, audit-green before any mutation."""
    root = tmp_path / "minijudge"
    shutil.copytree(MINIJUDGE, root)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "--allow-empty", "-m", "x"], cwd=root, check=True)
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root,
                         capture_output=True, text=True, check=True).stdout.strip()
    claims = root / "docs/claims.yaml"
    claims.write_text(re.sub(r"harness_commit: \S+", f"harness_commit: {sha}",
                             claims.read_text()))
    return root


# --- success criterion 1+2: green audit, correctly identified ---------------

def test_minijudge_audit_holds_every_contract(tmp_path, capsys):
    rc = _audit(MINIJUDGE, tmp_path)

    assert rc == 0
    assert "all contracts hold" in capsys.readouterr().out
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["contracts"]["holds"] is True
    assert manifest["contracts"]["findings"] == []


def test_minijudge_manifest_identifies_the_consumer_not_groundtruth(tmp_path):
    _audit(MINIJUDGE, tmp_path)

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["evaluation"]["name"] == "minijudge"
    assert manifest["evaluation"]["version"] == "0.1.0"


def test_name_flag_defaults_to_groundtruth_for_the_host_repo(tmp_path):
    rc = main(["audit",
               "--out", str(tmp_path / "m.json"), "--report", str(tmp_path / "a.md")])

    assert rc == 0
    manifest = json.loads((tmp_path / "m.json").read_text())
    assert manifest["evaluation"]["name"] == "groundtruth"


# --- success criterion 3: byte-determinism (CT10 parity) ---------------------

def test_minijudge_audit_outputs_are_byte_identical_across_runs(tmp_path):
    (tmp_path / "one").mkdir()
    (tmp_path / "two").mkdir()

    assert _audit(MINIJUDGE, tmp_path / "one") == 0
    assert _audit(MINIJUDGE, tmp_path / "two") == 0

    for fname in ("manifest.json", "assurance.md"):
        first = (tmp_path / "one" / fname).read_bytes()
        second = (tmp_path / "two" / fname).read_bytes()
        assert first == second, f"{fname} not byte-deterministic"


# --- success criterion 5: no consumer literal in the engine ------------------

def test_engine_contains_no_consumer_literal():
    engine_files = sorted((REPO_ROOT / "groundtruth/meta").glob("*.py"))
    engine_files.append(REPO_ROOT / "groundtruth/cli.py")

    assert len(engine_files) > 5
    for path in engine_files:
        assert "minijudge" not in path.read_text().lower(), (
            f"consumer literal leaked into the engine: {path.name}")


def test_minijudge_metric_artifact_is_script_produced(tmp_path):
    """The committed agreement.json is exactly what scripts/judge.py emits —
    the metric evidence is real, not hand-typed."""
    committed = (MINIJUDGE / "runs/agreement.json").read_bytes()

    out = subprocess.run(
        [sys.executable, "scripts/judge.py", "--out", str(tmp_path / "agreement.json")],
        cwd=MINIJUDGE, capture_output=True, text=True)

    assert out.returncode == 0, out.stderr
    assert (tmp_path / "agreement.json").read_bytes() == committed


# --- success criterion 6: negative controls (non-vacuous) --------------------

def _findings(capsys) -> str:
    return capsys.readouterr().out


def test_control_metric_lie_fails_ct5(minijudge_copy, tmp_path, capsys):
    claims = minijudge_copy / "docs/claims.yaml"
    claims.write_text(claims.read_text().replace("value: 0.75", "value: 0.99"))

    assert _audit(minijudge_copy, tmp_path) == 1
    assert "[CT5]" in _findings(capsys)


def test_control_missing_falsification_fails_ct2(minijudge_copy, tmp_path, capsys):
    claims = minijudge_copy / "docs/claims.yaml"
    claims.write_text(claims.read_text().replace(
        "falsification:", "falsification_removed:", 1))

    assert _audit(minijudge_copy, tmp_path) == 1
    assert "[CT2]" in _findings(capsys)


def test_control_orphaned_threat_ref_fails_ct4(minijudge_copy, tmp_path, capsys):
    claims = minijudge_copy / "docs/claims.yaml"
    claims.write_text(claims.read_text().replace(
        "threat_refs: [T1, T2]", "threat_refs: [T1, T2, T9]"))

    assert _audit(minijudge_copy, tmp_path) == 1
    out = _findings(capsys)
    assert "[CT4]" in out and "T9" in out


def test_control_deleted_evidence_artifact_fails_ct1(minijudge_copy, tmp_path, capsys):
    (minijudge_copy / "runs/agreement.json").unlink()

    assert _audit(minijudge_copy, tmp_path) == 1
    assert "[CT1]" in _findings(capsys)


def test_control_invalid_threat_status_fails_ct7(minijudge_copy, tmp_path, capsys):
    threats = minijudge_copy / "docs/threats.yaml"
    threats.write_text(threats.read_text().replace(
        "status: mitigated", "status: wontfix", 1))

    assert _audit(minijudge_copy, tmp_path) == 1
    assert "[CT7]" in _findings(capsys)


def test_control_prose_register_divergence_fails_ct8(minijudge_copy, tmp_path, capsys):
    prose = minijudge_copy / "docs/THREATS_TO_VALIDITY.md"
    lines = [l for l in prose.read_text().splitlines() if not l.startswith("| T3 ")]
    prose.write_text("\n".join(lines) + "\n")

    assert _audit(minijudge_copy, tmp_path) == 1
    assert "[CT8]" in _findings(capsys)


def test_control_malformed_claims_register_exits_2(minijudge_copy, tmp_path, capsys):
    (minijudge_copy / "docs/claims.yaml").write_text("claims: 3\n")

    assert _audit(minijudge_copy, tmp_path) == 2
    assert "claims.yaml" in capsys.readouterr().err


def test_control_missing_threats_register_exits_2(minijudge_copy, tmp_path, capsys):
    (minijudge_copy / "docs/threats.yaml").unlink()

    assert _audit(minijudge_copy, tmp_path) == 2
    assert "threats.yaml" in capsys.readouterr().err
