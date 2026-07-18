"""Steward loader: schema-v1 declarations reader (no YAML dependency — the
steward is stdlib-only by law RC5) + the enumerated read-only git surface."""
import subprocess
from pathlib import Path

import pytest

from groundtruth.steward.loader import (
    DeclarationError,
    git_diff_names,
    git_index,
    git_object_exists,
    load_constitution,
    load_debt,
    parse_document,
)

CONSTITUTION = """# Constitution

Law prose here.

```yaml
constitution_schema: 1
roles:
  - {pattern: "docs/adr/*.md", role: adr, lifecycle: living}
  - {pattern: "runs/**", role: evidence, lifecycle: derived}
version_anchors:
  - {file: "pyproject.toml", pattern: "^version = \\"([^\\"]+)\\""}
derived_artifacts:
  - {path: "runs/m.json", regen: "groundtruth steward"}
frozen:
  - {path: "examples/minijudge", commit: "deadbeef"}
layer_rules:
  - {kind: forbid, src: "groundtruth.core", dst: "groundtruth.products"}
exemptions: []
```
"""


def test_parse_document_scalars_comments_empty_list_and_flow_items():
    doc = parse_document(
        "# comment\nconstitution_schema: 1\nexemptions: []\n"
        "roles:\n"
        '  - {pattern: "docs/adr/*.md", role: adr, lifecycle: living}\n'
        '  - {pattern: "runs/**", role: evidence, lifecycle: derived}\n'
    )
    assert doc["constitution_schema"] == 1
    assert doc["exemptions"] == []
    assert doc["roles"][1] == {
        "pattern": "runs/**", "role": "evidence", "lifecycle": "derived"
    }


def test_flow_quoted_strings_keep_commas_colons_dashes_and_lists_nest():
    doc = parse_document(
        "items:\n"
        '  - {id: 7, title: "a, b: c — d", evidence: ["x.md", "y.md"], resolution: ""}\n'
    )
    item = doc["items"][0]
    assert item["id"] == 7
    assert item["title"] == "a, b: c — d"
    assert item["evidence"] == ["x.md", "y.md"]
    assert item["resolution"] == ""


def test_load_constitution_parses_the_embedded_block(tmp_path):
    p = tmp_path / "CONSTITUTION.md"
    p.write_text(CONSTITUTION)
    d = load_constitution(p)
    assert d.schema == 1
    assert d.roles[0]["role"] == "adr"
    assert d.frozen[0]["commit"] == "deadbeef"
    assert d.exemptions == ()


def test_load_constitution_rejects_missing_block_missing_key_and_seventh_key(tmp_path):
    p = tmp_path / "CONSTITUTION.md"
    p.write_text("# no declarations here\n")
    with pytest.raises(DeclarationError):
        load_constitution(p)
    p.write_text(CONSTITUTION.replace("exemptions: []\n", ""))
    with pytest.raises(DeclarationError):
        load_constitution(p)
    p.write_text(CONSTITUTION.replace("exemptions: []", "exemptions: []\nextra_key: 1"))
    with pytest.raises(DeclarationError):  # a seventh schema key is H0 evidence
        load_constitution(p)


def test_load_debt_validates_schema_and_state_vocabulary(tmp_path):
    p = tmp_path / "debt.yaml"
    p.write_text(
        "debt_schema: 1\nitems:\n"
        '  - {id: 1, title: "t", category: infra, state: resolved, origin: "v0.1", evidence: ["README.md"], resolution: "README.md"}\n'
    )
    items = load_debt(p)
    assert items[0]["state"] == "resolved"
    p.write_text(p.read_text().replace("state: resolved", "state: wontfix"))
    with pytest.raises(DeclarationError):
        load_debt(p)
    p.write_text("debt_schema: 1\nitems:\n  - {id: 2, title: \"t\"}\n")
    with pytest.raises(DeclarationError):  # missing required fields
        load_debt(p)


@pytest.fixture()
def repo(tmp_path):
    def git(*args):
        subprocess.run(
            ["git", *args], cwd=tmp_path, check=True, capture_output=True
        )
    git("init", "-q")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    (tmp_path / "a.txt").write_text("one\n")
    git("add", "-A")
    git("commit", "-q", "-m", "c1")
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True
    ).stdout.strip()
    return tmp_path, sha


def test_git_index_is_sorted_and_complete(repo):
    root, _ = repo
    (root / "b.txt").write_text("two\n")
    subprocess.run(["git", "add", "b.txt"], cwd=root, check=True, capture_output=True)
    assert git_index(root) == ("a.txt", "b.txt")


def test_git_diff_names_sees_working_tree_edits_and_object_exists(repo):
    root, sha = repo
    assert git_diff_names(root, sha, "a.txt") == ()
    (root / "a.txt").write_text("one!\n")  # uncommitted single-byte-class edit
    assert git_diff_names(root, sha, "a.txt") == ("a.txt",)
    assert git_object_exists(root, sha)
    assert not git_object_exists(root, "0" * 40)


def test_git_index_on_this_repo_contains_known_files():
    root = Path(__file__).resolve().parents[1]
    index = git_index(root)
    assert "README.md" in index
    assert list(index) == sorted(index)
