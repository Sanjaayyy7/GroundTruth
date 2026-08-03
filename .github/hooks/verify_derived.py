"""Pre-commit gate: every derived artifact must regenerate byte-identically
from the STAGED tree.

Why this exists as a hook and not as a test. `groundtruth steward` builds its
manifest from git *index* blobs (`steward/loader.py::git_blob_sizes`), never
from the working tree. Run it before `git add` and it records the sizes of the
previous revision; the working tree still holds the newer file, so `pytest`
passes locally and CI — which sees only what was committed — fails. No test
can catch that, because the defect is an ordering between staging and
regeneration, and the test suite has no opinion about the index.

Why the regeneration loops. The manifest lists itself. Staging a freshly
regenerated manifest changes the very blob whose size that manifest records,
so a single regenerate-then-stage leaves the artifact describing its own
previous version. Measured on this repository: pass 1 leaves 2 files drifting,
pass 2 leaves 0. The loop is bounded (MAX_PASSES) and fails loudly rather than
spinning — a manifest that will not reach a fixed point is a finding about the
manifest, not a reason to retry forever.

Two tiers, deliberately:
  * REGEN artifacts are bookkeeping — manifests, the assurance and steward
    reports, the HTML render. They carry no new measurement, so the hook
    regenerates and stages them for you.
  * GATE artifacts are measurements — scorecards, detector quality. Those are
    checked read-only and fail the commit. A changed measurement is a result,
    and results get staged by a human who meant it.

Runs the same commands as .github/workflows/ci.yml. Kept to the sub-second
verbs; the test suite is not in here on purpose, because a 30-second
pre-commit hook gets uninstalled.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

MAX_PASSES = 5

#: Directories holding committed derived artifacts, i.e. what CI byte-diffs.
ARTIFACT_ROOTS: tuple[str, ...] = ("runs", "examples/minijudge/runs")

#: Bookkeeping regenerations, in dependency order: the steward manifest sizes
#: every other tracked blob, so it runs last.
REGEN: tuple[tuple[str, ...], ...] = (
    ("audit",),
    ("audit", "--root", "examples/minijudge", "--name", "minijudge"),
    ("report",),
    ("steward",),
)

#: Read-only measurement gates. Each must exit 0 against the staged tree.
GATES: tuple[tuple[str, ...], ...] = (("rescore", "--check"),)


class NotConverged(RuntimeError):
    """Regeneration never reached a fixed point within MAX_PASSES."""


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit("[derived] not inside a git work tree")
    return Path(proc.stdout.strip()).resolve()


def groundtruth(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI so that it resolves *this* checkout, not whichever tree
    the editable install happens to point at. GROUNDTRUTH_ROOT is the override
    the CLI already documents (`cli.py::_repo_root`)."""
    return subprocess.run(
        [sys.executable, "-m", "groundtruth.cli", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "GROUNDTRUTH_ROOT": str(root)},
    )


def drifting(root: Path, roots: Sequence[str]) -> list[str]:
    """Tracked paths whose working-tree bytes differ from the index."""
    proc = _git(root, "diff", "--name-only", "--", *roots)
    if proc.returncode != 0:
        raise SystemExit(f"[derived] git diff failed: {proc.stderr.strip()}")
    return sorted(p for p in proc.stdout.splitlines() if p)


def stage(root: Path, paths: Sequence[str]) -> None:
    proc = _git(root, "add", "--", *paths)
    if proc.returncode != 0:
        raise SystemExit(f"[derived] git add failed: {proc.stderr.strip()}")


def regenerate_all(root: Path) -> None:
    for argv in REGEN:
        proc = groundtruth(root, *argv)
        # `audit` exits 1 on contract findings and `steward` exits 1 on
        # repository findings; both still write their artifacts, and both are
        # already gated by their own CI steps. Only exit 2 (could not run) is
        # fatal here, because then the artifact was never written.
        if proc.returncode == 2:
            sys.stdout.write(proc.stdout)
            sys.stderr.write(proc.stderr)
            raise SystemExit(f"[derived] `groundtruth {' '.join(argv)}` could not run")


def converge(
    root: Path,
    regenerate: Callable[[Path], None] = regenerate_all,
    roots: Sequence[str] = ARTIFACT_ROOTS,
    max_passes: int = MAX_PASSES,
) -> tuple[int, list[str]]:
    """Regenerate → stage → regenerate until a regeneration produces no drift.

    Returns (passes_used, everything_staged). Raises NotConverged if the
    artifacts never reach a fixed point.
    """
    staged: list[str] = []
    for attempt in range(1, max_passes + 1):
        regenerate(root)
        drift = drifting(root, roots)
        if not drift:
            return attempt, staged
        print(f"[derived] pass {attempt}: regenerated {len(drift)} artifact(s), staging")
        stage(root, drift)
        staged += [p for p in drift if p not in staged]
    raise NotConverged(
        f"derived artifacts still differ after {max_passes} regenerate/stage passes: "
        f"{', '.join(drifting(root, roots))}. A declared artifact that has no fixed "
        f"point is a defect in the artifact, not a reason to retry."
    )


def run_gates(root: Path) -> list[str]:
    """Read-only measurement checks. Returns the failures, human-readable."""
    failures = []
    for argv in GATES:
        proc = groundtruth(root, *argv)
        if proc.returncode != 0:
            failures.append(f"`groundtruth {' '.join(argv)}` exited {proc.returncode}")
            sys.stdout.write(proc.stdout)
            sys.stderr.write(proc.stderr)

    # detector-quality.json is a measurement, so it is regenerated to a scratch
    # path and compared — never written over the committed copy.
    committed = root / "runs/detector-quality.json"
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / "detector-quality.json"
        proc = groundtruth(root, "validate", "--out", str(fresh))
        if proc.returncode != 0:
            failures.append(f"`groundtruth validate` exited {proc.returncode}")
            sys.stderr.write(proc.stderr)
        elif not committed.exists():
            failures.append("runs/detector-quality.json is missing")
        elif fresh.read_bytes() != committed.read_bytes():
            failures.append(
                "runs/detector-quality.json is stale — regenerate with "
                "`groundtruth validate --out runs/detector-quality.json`, "
                "then stage it deliberately (it is a measurement)"
            )
    return failures


#: Attribution markers. The public surface of this repository carries none of
#: these, and a grep run by hand before a push is a policy enforced by memory.
#: Blocking at commit time is cheap; rewriting published history is not, because
#: this project's headline claims are SHA-addressed and a rewrite dangles every
#: one of them.
_ATTRIBUTION = ("co-authored-by:", "generated with", "claude", "anthropic", "copilot")


#: This file states the markers, so it necessarily contains them. A rule's
#: definition is not an instance of the thing it forbids, and exempting it is
#: narrower than the alternatives — obfuscating the markers would make the
#: policy unreadable, and reading them from a data file would just move the
#: same self-reference one hop.
_SELF = "/".join(Path(__file__).parts[-3:])


def scan_attribution(root: Path) -> list[str]:
    """Staged content carrying tool attribution, as 'path:line' strings."""
    names = _git(root, "diff", "--cached", "--name-only", "--diff-filter=ACM")
    hits: list[str] = []
    for path in [p for p in names.stdout.splitlines() if p.strip() and p != _SELF]:
        blob = _git(root, "show", f":{path}")
        if blob.returncode:
            continue  # unreadable in the index (submodule, deletion): not ours to judge
        for lineno, line in enumerate(blob.stdout.splitlines(), 1):
            low = line.lower()
            if any(marker in low for marker in _ATTRIBUTION):
                hits.append(f"{path}:{lineno}: {line.strip()[:90]}")
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verify_derived", description=__doc__)
    parser.add_argument(
        "--max-passes",
        type=int,
        default=MAX_PASSES,
        help=f"bound on the regenerate/stage loop (default {MAX_PASSES})",
    )
    parser.add_argument(
        "--attribution-scan",
        action="store_true",
        help="only scan staged content for tool attribution, then exit",
    )
    args = parser.parse_args(argv)
    root = repo_root()

    if args.attribution_scan:
        hits = scan_attribution(root)
        if hits:
            print("[attribution] staged content carries tool attribution:", file=sys.stderr)
            for hit in hits:
                print(f"  x {hit}", file=sys.stderr)
            return 1
        print("[attribution] staged content is clean")
        return 0

    failures = run_gates(root)
    if failures:
        print("[derived] MEASUREMENT GATE FAILED", file=sys.stderr)
        for f in failures:
            print(f"  x {f}", file=sys.stderr)
        return 1

    try:
        passes, staged = converge(root, max_passes=args.max_passes)
    except NotConverged as exc:
        print(f"[derived] {exc}", file=sys.stderr)
        return 1

    if staged:
        print(f"[derived] staged {len(staged)} regenerated artifact(s) in {passes} pass(es):")
        for path in staged:
            print(f"    + {path}")
    else:
        print(f"[derived] all derived artifacts already byte-fresh ({passes} pass)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
