"""Evaluation Contracts — pure invariants over the graph, one planted
violation per contract. Findings are explanatory objects, never scores."""
from conftest import green_nodes

from groundtruth.meta.contracts import CONTRACTS, CONTRACTS_DOC, run_contracts
from groundtruth.meta.graph import build_graph
from groundtruth.meta.model import EvidenceNode


def findings_for(nodes):
    return run_contracts(build_graph(nodes))


def replace(nodes, node_id, **attr_updates):
    out = []
    for n in nodes:
        if n.id == node_id:
            out.append(EvidenceNode(n.id, n.kind, n.provenance, {**n.attrs, **attr_updates}))
        else:
            out.append(n)
    return out


def ids(findings):
    return {f.contract_id for f in findings}


def test_green_fixture_has_zero_findings():
    assert findings_for(green_nodes()) == []


def test_ct1_missing_evidence_artifact():
    nodes = replace(green_nodes(), "artifact:data/a.txt", exists=False)
    assert "CT1" in ids(findings_for(nodes))


def test_ct2_missing_falsification():
    nodes = replace(green_nodes(), "claim:C1", falsification="")
    assert "CT2" in ids(findings_for(nodes))


def test_ct3_fact_without_reproduce():
    nodes = replace(green_nodes(), "claim:C1", reproduce="")
    assert "CT3" in ids(findings_for(nodes))


def test_ct3_vocabulary_violation():
    nodes = replace(green_nodes(), "claim:C1", classification="vibes")
    assert "CT3" in ids(findings_for(nodes))


def test_ct4_dangling_threat_ref():
    nodes = replace(green_nodes(), "claim:C1", threat_refs=["T9"])
    assert "CT4" in ids(findings_for(nodes))


def test_ct4_one_way_reference():
    nodes = replace(green_nodes(), "threat:T1", claim_refs=[])
    assert "CT4" in ids(findings_for(nodes))


def test_ct5_metric_mismatch():
    nodes = replace(green_nodes(), "claim:C1", metrics_resolved=[
        {"name": "p", "value": 0.5, "source": "data/m.json", "path": "p", "actual": 0.4}])
    assert "CT5" in ids(findings_for(nodes))


def test_ct6_version_drift():
    nodes = replace(green_nodes(), "version:abc", readme_version="0.5")
    assert "CT6" in ids(findings_for(nodes))


def test_ct6_commit_not_in_git():
    nodes = replace(green_nodes(), "version:abc", exists_in_git=False)
    assert "CT6" in ids(findings_for(nodes))


def test_ct7_resolved_without_evidence():
    nodes = replace(green_nodes(), "threat:T1", evidence_paths=[])
    assert "CT7" in ids(findings_for(nodes))


def test_ct8_prose_register_id_drift():
    nodes = replace(green_nodes(), "artifact:docs/THREATS_TO_VALIDITY.md",
                    prose_threat_ids=["T1", "T2"])
    assert "CT8" in ids(findings_for(nodes))


def test_ct9_observation_without_confounds():
    nodes = replace(green_nodes(), "claim:C1",
                    classification="supported_observation", confounds_remaining=[])
    assert "CT9" in ids(findings_for(nodes))


def test_contract_docs_cover_ct1_through_ct10():
    assert set(CONTRACTS_DOC) == {f"CT{i}" for i in range(1, 11)}
    assert {c.id for c in CONTRACTS} == {f"CT{i}" for i in range(1, 10)}


def test_findings_are_deterministically_ordered():
    nodes = replace(green_nodes(), "claim:C1", falsification="", reproduce="")
    f = findings_for(nodes)
    assert f == sorted(f, key=lambda x: (x.contract_id, x.node_id))
