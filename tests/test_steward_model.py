"""Steward model: Finding + RepoDeclarations, deliberately parallel to
meta/'s model (ADR-0008 D5 — duplication over coupling)."""
import dataclasses

import pytest

from groundtruth.steward.model import DeclarationError, Finding, RepoDeclarations


def test_finding_is_frozen_and_sorts_by_check_path_line():
    f1 = Finding(check_id="RC2", path="docs/a.md", summary="broken link", line=3)
    f2 = Finding(check_id="RC1", path="zzz.txt", summary="no role rule matches")
    f3 = Finding(check_id="RC2", path="docs/a.md", summary="other", line=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        f1.path = "x"  # type: ignore[misc]
    assert sorted([f1, f2, f3], key=lambda f: f.sort_key()) == [f2, f3, f1]
    assert f2.line == 0  # whole-file finding


def test_declarations_hold_tuples_and_schema():
    d = RepoDeclarations(
        schema=1,
        roles=({"pattern": "docs/adr/*.md", "role": "adr", "lifecycle": "living"},),
        version_anchors=(), derived_artifacts=(), frozen=(),
        layer_rules=(), exemptions=(),
    )
    assert d.schema == 1
    assert d.roles[0]["role"] == "adr"


def test_declaration_error_is_an_exception():
    assert issubclass(DeclarationError, Exception)
