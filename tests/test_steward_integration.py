"""The real repository under its own Constitution: green at HEAD (RC1-RC8
including the ADR-0001 layering law, unenforced for 8 milestones before
this), committed artifacts byte-fresh, and the size-budget law (ADR-0008
falsification trigger)."""
from pathlib import Path

from groundtruth.cli import main

REPO = Path(__file__).resolve().parents[1]


def test_repository_contracts_hold_at_head(tmp_path, capsys):
    assert main(["steward", "--root", str(REPO), "--out", str(tmp_path)]) == 0


def test_committed_steward_artifacts_are_byte_fresh(tmp_path, capsys):
    main(["steward", "--root", str(REPO), "--out", str(tmp_path)])
    for name in ("repo-manifest.json", "steward-report.md"):
        regenerated = (tmp_path / name).read_bytes()
        committed = (REPO / "runs/steward" / name).read_bytes()
        assert regenerated == committed, f"{name} is stale — rerun: groundtruth steward"


def test_size_budget_law_adr_0008():
    steward = sorted((REPO / "groundtruth/steward").glob("*.py"))
    tests = sorted((REPO / "tests").glob("test_steward*.py"))
    total = sum(len(p.read_text().splitlines()) for p in steward + tests)
    assert total <= 1496, (
        f"steward + tests = {total} lines > 2x meta/ (1496): "
        "ADR-0008 falsification trigger fires"
    )
