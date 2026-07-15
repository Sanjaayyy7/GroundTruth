"""Quality manifest — sibling assessment 1: what evidence exists. Deterministic."""
from conftest import green_nodes

from groundtruth.meta.contracts import run_contracts
from groundtruth.meta.graph import build_graph
from groundtruth.meta.manifest import build_manifest, render_manifest


def _manifest():
    g = build_graph(green_nodes())
    return build_manifest(g, run_contracts(g)), g


def test_manifest_core_fields():
    m, g = _manifest()
    assert m["manifest_schema_version"] == 1
    assert m["evaluation"]["version"] == "0.6.0"
    assert m["registers"]["claims"]["by_classification"] == {"fact": 1}
    assert m["contracts"]["holds"] is True
    assert set(m["dimensions"]) == {f"D{i:02d}_" + s for i, s in [
        (1, "determinism"), (2, "reproducibility"), (3, "detector_quality"),
        (4, "label_quality"), (5, "dataset_discrimination"), (6, "threat_coverage"),
        (7, "statistical_support"), (8, "claim_traceability"),
        (9, "version_stability"), (10, "experimental_rigor")]}


def test_no_composite_score_anywhere():
    m, _ = _manifest()
    assert "no_composite_score" in m
    flat = str(m).lower()
    assert "quality_score" not in flat and "overall_score" not in flat


def test_traceability_reports_counts_not_scores():
    m, _ = _manifest()
    d8 = m["dimensions"]["D08_claim_traceability"]
    assert d8["value"] == {"traced": 1, "total": 1}


def test_render_is_byte_deterministic():
    m1, _ = _manifest()
    m2, _ = _manifest()
    assert render_manifest(m1) == render_manifest(m2)
    assert render_manifest(m1).endswith("\n")


def test_findings_embedded_when_contracts_fail():
    from groundtruth.meta.contracts import Finding
    g = build_graph(green_nodes())
    m = build_manifest(g, [Finding("CT1", "claim:C1", "boom")])
    assert m["contracts"]["holds"] is False
    assert m["contracts"]["findings"][0]["summary"] == "boom"
