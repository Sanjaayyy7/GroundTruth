"""Steward report: byte-deterministic manifest JSON + markdown report with
the R3 exemption instrument."""
from groundtruth.steward.model import Finding, RepoDeclarations
from groundtruth.steward.report import render_manifest, render_report

INV = {
    "manifest_schema": 1,
    "files": [{"path": "a.md", "role": "doc", "lifecycle": "living", "bytes": 3}],
    "roles": {"doc": {"files": 1, "bytes": 3}},
    "total": {"files": 1, "bytes": 3},
}


def _decls(exemptions=()):
    return RepoDeclarations(
        schema=1, roles=(), version_anchors=(), derived_artifacts=(),
        frozen=(), layer_rules=(), exemptions=tuple(exemptions),
    )


def test_manifest_json_sorted_keys_trailing_newline_and_stable():
    text = render_manifest(INV)
    assert text.endswith("\n")
    assert text.index('"files"') < text.index('"manifest_schema"') < text.index('"roles"')
    assert render_manifest(INV) == text


def test_report_green_wording_and_determinism():
    text = render_report((), (), _decls(), INV)
    assert "all repository contracts hold" in text
    assert "active exemptions: 0" in text
    assert render_report((), (), _decls(), INV) == text
    assert "\r" not in text


def test_report_lists_findings_and_exemption_instrument():
    active = (Finding("RC2", "docs/a.md", "unresolved reference: x.md", 3),)
    exempted = (Finding("RC1", "zzz.bin", "no role rule matches this tracked path"),)
    decls = _decls(
        [{"check": "RC1", "path": "zzz.bin", "justification": "fixture", "milestone": "v0.8"}]
    )
    text = render_report(active, exempted, decls, INV)
    assert "[RC2] docs/a.md:3 — unresolved reference: x.md" in text
    assert "active exemptions: 1" in text
    assert "RC1 zzz.bin (since v0.8) — fixture" in text
    assert "exempted findings: 1" in text
