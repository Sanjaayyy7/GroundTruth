"""groundtruth steward — rc semantics (0 clean / 1 findings / 2 declaration
error), byte parity across runs, zero mutation outside the out dir."""
from test_steward_checks import _git, make_repo

from groundtruth.cli import main


def test_rc0_writes_both_artifacts_and_reports_green(tmp_path, capsys):
    root = make_repo(tmp_path / "r")
    out = tmp_path / "out"
    assert main(["steward", "--root", str(root), "--out", str(out)]) == 0
    assert "all repository contracts hold" in capsys.readouterr().out
    assert (out / "repo-manifest.json").exists()
    assert "all repository contracts hold" in (out / "steward-report.md").read_text()


def test_rc1_when_a_contract_finding_exists(tmp_path, capsys):
    root = make_repo(tmp_path / "r")
    (root / "zzz.bin").write_text("x")
    _git(root, "add", "zzz.bin")
    assert main(["steward", "--root", str(root), "--out", str(tmp_path / "o")]) == 1
    assert "[RC1] zzz.bin" in capsys.readouterr().out


def test_rc2_on_malformed_declarations(tmp_path, capsys):
    root = make_repo(tmp_path / "r")
    p = root / "docs/CONSTITUTION.md"
    p.write_text(p.read_text().replace("constitution_schema: 1", "bad_key: 1"))
    assert main(["steward", "--root", str(root), "--out", str(tmp_path / "o")]) == 2


def test_byte_parity_across_consecutive_runs(tmp_path, capsys):
    root = make_repo(tmp_path / "r")
    a, b = tmp_path / "a", tmp_path / "b"
    main(["steward", "--root", str(root), "--out", str(a)])
    main(["steward", "--root", str(root), "--out", str(b)])
    for name in ("repo-manifest.json", "steward-report.md"):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_zero_mutation_outside_the_out_dir(tmp_path, capsys):
    root = make_repo(tmp_path / "r")
    before = {
        p: p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()
    }
    main(["steward", "--root", str(root), "--out", str(tmp_path / "o")])
    after = {p: p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}
    assert before == after
