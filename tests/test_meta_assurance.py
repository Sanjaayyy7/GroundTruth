"""Assurance report — sibling assessment 2: what conclusions are justified."""
from conftest import green_nodes

from groundtruth.meta.assurance import render_assurance
from groundtruth.meta.contracts import Finding, run_contracts
from groundtruth.meta.graph import build_graph


def test_report_sections_and_placement():
    g = build_graph(green_nodes())
    text = render_assurance(g, run_contracts(g))
    assert "## Strongly supported" in text
    assert "claim:C1" in text.split("## Strongly supported")[1].split("##")[0]
    assert "All contracts hold." in text
    assert "No aggregate verdict" in text


def test_claim_with_finding_is_not_strongly_supported():
    g = build_graph(green_nodes())
    text = render_assurance(g, [Finding("CT1", "claim:C1", "evidence missing")])
    strong = text.split("## Strongly supported")[1].split("##")[0]
    assert "claim:C1" not in strong
    assert "evidence missing" in text


def test_report_is_deterministic():
    g = build_graph(green_nodes())
    f = run_contracts(g)
    assert render_assurance(g, f) == render_assurance(g, f)


def test_no_grades_no_scores():
    g = build_graph(green_nodes())
    text = render_assurance(g, run_contracts(g)).lower()
    for banned in ("health", "score:", "grade", "92.", "/10"):
        assert banned not in text
