"""The pre-commit derived-artifact gate (.github/hooks/verify_derived.py).

The gate exists because `groundtruth steward` reads git *index* blobs: run it
before `git add` and the manifest records the previous revision, which passes
locally and fails on a fresh checkout. The property under test is the one the
suite structurally could not express before — a single regenerate-then-stage is
NOT enough, because the manifest lists itself and staging it changes the blob
whose size it just recorded.

The fixture reproduces exactly that self-reference in miniature (an artifact
whose content is the size of every staged blob, itself included) so the loop
can be pinned in milliseconds without regenerating the real corpus.
"""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "verify_derived", REPO / ".github/hooks/verify_derived.py"
)
assert _SPEC and _SPEC.loader
hook = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(hook)


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return proc.stdout


def _self_sizing_manifest(root: Path) -> None:
    """The steward's mechanism in miniature: sizes come from the index, and the
    manifest is itself an indexed file, so writing it invalidates its own entry."""
    lines = []
    for record in _git(root, "ls-files", "-s").splitlines():
        meta, path = record.split("\t", 1)
        size = _git(root, "cat-file", "-s", meta.split()[1]).strip()
        lines.append(f"{path} {size}")
    (root / "manifest.txt").write_text("\n".join(lines) + "\n")


@pytest.fixture()
def staged_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    (root / "payload.txt").write_text("one\n")
    (root / "manifest.txt").write_text("placeholder\n")
    _git(root, "add", "-A")
    _self_sizing_manifest(root)
    _git(root, "add", "-A")
    _self_sizing_manifest(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "seed")
    # The commit under test: a source file changes and is staged, exactly as a
    # developer would stage it, leaving the derived manifest stale.
    (root / "payload.txt").write_text("one\ntwo\nthree\n")
    _git(root, "add", "payload.txt")
    return root


def test_converges_and_leaves_zero_drift(staged_repo: Path) -> None:
    passes, staged = hook.converge(
        staged_repo, regenerate=_self_sizing_manifest, roots=["."]
    )
    assert "manifest.txt" in staged
    assert hook.drifting(staged_repo, ["."]) == []
    assert passes >= 2


def test_one_pass_is_not_enough(staged_repo: Path) -> None:
    """The regression this hook exists for: regenerate-then-stage, once, leaves
    the manifest describing its own previous version."""
    with pytest.raises(hook.NotConverged):
        hook.converge(
            staged_repo, regenerate=_self_sizing_manifest, roots=["."], max_passes=1
        )


def test_non_convergence_fails_loudly_rather_than_spinning(staged_repo: Path) -> None:
    def never_settles(root: Path) -> None:
        prior = (root / "manifest.txt").read_text()
        (root / "manifest.txt").write_text(prior + "x\n")

    with pytest.raises(hook.NotConverged, match="no fixed point"):
        hook.converge(staged_repo, regenerate=never_settles, roots=["."], max_passes=3)


def test_hook_runs_the_same_verbs_as_ci() -> None:
    """The hook is only a guard if it mirrors CI. Pin the correspondence so a
    new CI step cannot silently escape the local gate."""
    ci = (REPO / ".github/workflows/ci.yml").read_text()
    for argv in hook.REGEN + hook.GATES:
        assert f"groundtruth {' '.join(argv)}" in ci, argv
