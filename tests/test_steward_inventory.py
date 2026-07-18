"""Steward inventory: ordered first-match role assignment + repo manifest."""
from groundtruth.steward.inventory import build_inventory, match_role

ROLES = (
    {"pattern": "docs/adr/*.md", "role": "adr", "lifecycle": "living"},
    {"pattern": "docs/**", "role": "doc", "lifecycle": "living"},
    {"pattern": "runs/**", "role": "evidence", "lifecycle": "derived"},
    {"pattern": "README.md", "role": "doc", "lifecycle": "living"},
)


def test_star_stays_within_a_directory_and_doublestar_crosses():
    assert match_role("docs/adr/0001-x.md", ROLES)["role"] == "adr"
    assert match_role("runs/steward/deep/file.json", ROLES)["role"] == "evidence"
    assert match_role("README.md", ROLES)["role"] == "doc"
    assert match_role("zzz/unknown.txt", ROLES) is None


def test_first_match_wins_in_declaration_order():
    # docs/adr/*.md files also match docs/** — the earlier, narrower rule wins
    assert match_role("docs/adr/0002-y.md", ROLES)["role"] == "adr"
    assert match_role("docs/STRATEGY.md", ROLES)["role"] == "doc"


def test_build_inventory_totals_files_and_bytes_per_role(tmp_path):
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "docs" / "adr" / "0001-a.md").write_text("12345")
    (tmp_path / "docs" / "notes.md").write_text("1234567")
    (tmp_path / "orphan.bin").write_text("xx")
    inv = build_inventory(
        tmp_path, ("docs/adr/0001-a.md", "docs/notes.md", "orphan.bin"), ROLES
    )
    assert inv["manifest_schema"] == 1
    assert inv["roles"]["adr"] == {"files": 1, "bytes": 5}
    assert inv["roles"]["doc"] == {"files": 1, "bytes": 7}
    files = {f["path"]: f for f in inv["files"]}
    assert files["orphan.bin"]["role"] is None
    assert [f["path"] for f in inv["files"]] == sorted(files)
