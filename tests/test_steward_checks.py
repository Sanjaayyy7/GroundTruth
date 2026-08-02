"""RC1–RC9 + the pre-registered negative controls (stewardship protocol,
2026-07-17): every planted violation must yield a named finding; the
unmutated fixture must be green; exemptions suppress visibly."""
import subprocess
from pathlib import Path

import pytest

from groundtruth.steward.checks import run_checks
from groundtruth.steward.loader import git_index, load_constitution, load_debt

CONSTITUTION = r'''# Fixture Constitution

```yaml
constitution_schema: 1
roles:
  - {pattern: "docs/CONSTITUTION.md", role: law, lifecycle: living}
  - {pattern: "docs/adr/*.md", role: adr, lifecycle: living}
  - {pattern: "docs/claims.yaml", role: register, lifecycle: living}
  - {pattern: "docs/debt.yaml", role: register, lifecycle: living}
  - {pattern: "docs/specs/*.md", role: spec, lifecycle: historical}
  - {pattern: "docs/*.md", role: doc, lifecycle: living}
  - {pattern: "pkg/**", role: code, lifecycle: living}
  - {pattern: "runs/**", role: evidence, lifecycle: derived}
  - {pattern: "frozen/**", role: consumer, lifecycle: frozen}
  - {pattern: "pyproject.toml", role: config, lifecycle: living}
  - {pattern: "README.md", role: doc, lifecycle: living}
version_anchors:
  - {file: "pyproject.toml", pattern: "^version = \"([^\"]+)\""}
  - {file: "README.md", pattern: "\*\*v([0-9.]+) — shipping\*\*"}
derived_artifacts:
  - {path: "runs/m.json", regen: "make m"}
frozen:
  - {path: "frozen", commit: "@FREEZE@"}
layer_rules:
  - {kind: forbid, src: "pkg.core", dst: "pkg.products"}
  - {kind: stdlib_only, src: "pkg.steward"}
  - {kind: only_importer, dst: "pkg.steward", allowed: ["pkg.cli"]}
exemptions: []
```
'''

FILES = {
    "docs/adr/0001-x.md": "# ADR 1\n\n## Review trigger\n\nWhen X changes.\n",
    "docs/GUIDE.md": (
        "# guide\n\nSee [adr](adr/0001-x.md) and `runs/m.json`.\n\n"
        "Micro precision 0.9545 (tp 42 / fp 2 / fn 5) at v0.1 on 2026-07-18.\n\n"
        "| metric | value |\n|---|---|\n| recall | 0.89 |\n| counts | 42/2/5 |\n"
    ),
    "docs/specs/0001-v01.md": "# v0.1 record\n\nShipped micro precision 0.9143.\n",
    "docs/claims.yaml": (
        "schema_version: 2\nclaims:\n  - id: C1\n"
        "    statement: rules reach micro precision 0.9545 on the fixture corpus\n"
        "    metrics:\n"
        "      - {name: micro_precision, value: 0.9545,"
        " source: runs/detector-quality.json, path: micro.precision}\n"
    ),
    "runs/detector-quality.json": (
        '{"micro": {"precision": 0.9545, "recall": 0.8936,'
        ' "tp": 42, "fp": 2, "fn": 5}}\n'
    ),
    "docs/debt.yaml": (
        "debt_schema: 1\nitems:\n"
        '  - {id: 1, title: "open item", category: x, state: open, origin: "v0.1", evidence: ["README.md"], resolution: ""}\n'
        '  - {id: 2, title: "done item", category: x, state: resolved, origin: "v0.1", evidence: [], resolution: "README.md"}\n'
    ),
    "README.md": "# demo\n\n**v0.1 — shipping**\n",
    "pyproject.toml": 'version = "0.1.0"\n',
    "runs/m.json": "{}\n",
    "frozen/data.txt": "immutable\n",
    "pkg/core/a.py": "import json\n",
    "pkg/products/b.py": "import pkg.core.a\n",
    "pkg/steward/s.py": "import re\n",
    "pkg/cli.py": "import pkg.steward.s\n",
}


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def make_repo(root):
    """Miniature constitution-governed repo (shared with the CLI tests)."""
    for rel, content in FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    (root / "docs/CONSTITUTION.md").write_text(CONSTITUTION)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@t")
    _git(root, "config", "user.name", "t")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "freeze")
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True
    ).stdout.strip()
    (root / "docs/CONSTITUTION.md").write_text(CONSTITUTION.replace("@FREEZE@", sha))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "declare freeze")
    return root


@pytest.fixture()
def repo(tmp_path):
    return make_repo(tmp_path)


def run(root):
    decls = load_constitution(root / "docs/CONSTITUTION.md")
    debt = load_debt(root / "docs/debt.yaml")
    return run_checks(root, decls, debt, git_index(root))


def _edit(root, rel, old, new):
    p = root / rel
    p.write_text(p.read_text().replace(old, new))


def test_baseline_fixture_is_green(repo):
    active, exempted = run(repo)
    assert active == ()
    assert exempted == ()


def test_rc1_control_unmatched_tracked_file(repo):
    (repo / "zzz.bin").write_text("x")
    _git(repo, "add", "zzz.bin")
    active, _ = run(repo)
    assert [(f.check_id, f.path) for f in active] == [("RC1", "zzz.bin")]


def test_rc2_skips_template_placeholders_in_backticks(repo):
    # discovered live: docs/REPRODUCIBILITY.md cites `runs/experiments/...-<date>/`
    _edit(
        repo, "docs/GUIDE.md",
        "`runs/m.json`", "`runs/m.json` and `runs/exp-<date>/out.json`",
    )
    active, _ = run(repo)
    assert active == ()


def test_rc2_control_broken_living_doc_link(repo):
    _edit(repo, "docs/GUIDE.md", "adr/0001-x.md", "adr/0009-missing.md")
    active, _ = run(repo)
    assert [(f.check_id, f.path) for f in active] == [("RC2", "docs/GUIDE.md")]
    assert active[0].line == 3
    assert "adr/0009-missing.md" in active[0].summary


def test_rc3_control_desynced_anchor(repo):
    _edit(repo, "README.md", "v0.1", "v0.2")
    active, _ = run(repo)
    assert [(f.check_id, f.path) for f in active] == [("RC3", "README.md")]


def test_rc4_control_removed_regeneration_command(repo):
    _edit(repo, "docs/CONSTITUTION.md", 'regen: "make m"', 'regen: ""')
    active, _ = run(repo)
    assert [(f.check_id, f.path) for f in active] == [("RC4", "runs/m.json")]


def test_rc5_control_forbidden_import_edges(repo):
    _edit(repo, "pkg/core/a.py", "import json", "import json\nimport pkg.products.b")
    _edit(repo, "pkg/steward/s.py", "import re", "import re\nimport pkg.core.a")
    active, _ = run(repo)
    got = {(f.check_id, f.path) for f in active}
    assert ("RC5", "pkg/core/a.py") in got  # forbid: core -> products
    assert ("RC5", "pkg/steward/s.py") in got  # stdlib_only violated
    assert all(check == "RC5" for check, _ in got)


def test_rc5_only_importer_rule(repo):
    _edit(repo, "pkg/products/b.py", "import pkg.core.a", "import pkg.steward.s")
    active, _ = run(repo)
    assert [(f.check_id, f.path) for f in active] == [("RC5", "pkg/products/b.py")]


def test_rc6_control_stripped_adr_trigger(repo):
    _edit(repo, "docs/adr/0001-x.md", "## Review trigger\n\n", "")
    active, _ = run(repo)
    assert [(f.check_id, f.path) for f in active] == [("RC6", "docs/adr/0001-x.md")]


def test_rc7_control_fake_debt_resolution_reference(repo):
    _edit(repo, "docs/debt.yaml", 'resolution: "README.md"', 'resolution: "no/such/path"')
    active, _ = run(repo)
    assert [(f.check_id, f.path) for f in active] == [("RC7", "docs/debt.yaml")]
    assert "no/such/path" in active[0].summary


def test_rc8_control_one_byte_edited_in_frozen_tree(repo):
    with (repo / "frozen/data.txt").open("a") as fh:
        fh.write("!")
    active, _ = run(repo)
    assert [(f.check_id, f.path) for f in active] == [("RC8", "frozen/data.txt")]


def test_rc9_control_drifted_numeric_claim_in_a_living_document(repo):
    """The exact drift the meta-engine exists to kill: prose keeps a number
    the artifact no longer produces (0.9545 -> stale 0.9333)."""
    _edit(repo, "docs/GUIDE.md", "0.9545", "0.9333")
    active, _ = run(repo)
    assert [(f.check_id, f.path) for f in active] == [("RC9", "docs/GUIDE.md")]
    assert active[0].line == 5
    assert "0.9333" in active[0].summary


def test_rc9_control_drifted_confusion_triple(repo):
    _edit(repo, "docs/GUIDE.md", "| 42/2/5 |", "| 42/3/5 |")
    active, _ = run(repo)
    assert [(f.check_id, f.path) for f in active] == [("RC9", "docs/GUIDE.md")]
    assert "42/3/5" in active[0].summary


def test_rc9_historical_record_keeps_the_number_it_shipped_with(repo):
    """docs/specs/* is `historical`: 0.9143 resolves to nothing today and
    must not fire — rewriting a shipped record would falsify it (Law 3)."""
    active, _ = run(repo)
    assert active == ()
    _edit(repo, "docs/specs/0001-v01.md", "0.9143", "0.9333")
    active, _ = run(repo)
    assert active == ()


def test_rc9_excludes_versions_dates_counts_indices_and_code(repo):
    _edit(
        repo, "docs/GUIDE.md", "# guide\n",
        "# guide\n\nv0.9.1 on 2026-08-02 touched 51 files, 3 of them at line 1234;\n"
        "see item 2 of 7. Fenced numbers are code, not prose:\n\n"
        "```\nprecision = 0.1111\n```\n\nand so is `micro.precision 0.2222`.\n",
    )
    active, _ = run(repo)
    assert active == ()


def test_rc9_allowlist_entry_without_a_reason_is_itself_a_finding(repo):
    _edit(repo, "docs/GUIDE.md", "0.9545", "0.9333")
    _edit(repo, "docs/CONSTITUTION.md", "constitution_schema: 1", "constitution_schema: 2")
    _edit(
        repo, "docs/CONSTITUTION.md", "exemptions: []",
        'exemptions: []\nnumeric_allowlist:\n'
        '  - {literal: "0.9333", path: "docs/GUIDE.md", reason: ""}',
    )
    active, _ = run(repo)
    assert [(f.check_id, f.path) for f in active] == [("RC9", "docs/CONSTITUTION.md")]
    assert "reason" in active[0].summary
    _edit(repo, "docs/CONSTITUTION.md", 'reason: ""', 'reason: "external paper threshold"')
    active, _ = run(repo)
    assert active == ()


def test_exemption_suppresses_visibly_not_silently(repo):
    (repo / "zzz.bin").write_text("x")
    _git(repo, "add", "zzz.bin")
    _edit(
        repo,
        "docs/CONSTITUTION.md",
        "exemptions: []",
        "exemptions:\n"
        '  - {check: RC1, path: "zzz.bin", justification: "fixture", milestone: "v0.8"}',
    )
    active, exempted = run(repo)
    assert active == ()
    assert [(f.check_id, f.path) for f in exempted] == [("RC1", "zzz.bin")]
