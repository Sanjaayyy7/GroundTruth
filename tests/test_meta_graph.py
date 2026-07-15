"""Evidence Graph — built from the model, never from raw YAML. Pure."""
from groundtruth.meta.graph import build_graph
from groundtruth.meta.model import EvidenceNode, Provenance

P = Provenance(source="fixture")


def _nodes():
    return [
        EvidenceNode("claim:C1", "claim", P, {
            "classification": "fact", "evidence_paths": ["data/a.txt"],
            "threat_refs": ["T1"],
        }),
        EvidenceNode("experiment:C1", "experiment", P, {"command": "x", "script_paths": {}}),
        EvidenceNode("threat:T1", "threat", P, {
            "status": "resolved", "claim_refs": ["C1"], "evidence_paths": ["data/a.txt"],
        }),
        EvidenceNode("artifact:data/a.txt", "artifact", P, {"exists": True}),
        EvidenceNode("version:abc", "version", P, {"exists_in_git": True}),
    ]


def test_edges_derived_from_attrs():
    g = build_graph(_nodes())
    kinds = {(e.src, e.kind, e.dst) for e in g.edges}
    assert ("claim:C1", "supported_by", "artifact:data/a.txt") in kinds
    assert ("claim:C1", "threatened_by", "threat:T1") in kinds
    assert ("threat:T1", "mitigated_by", "artifact:data/a.txt") in kinds
    assert ("claim:C1", "reproduced_by", "experiment:C1") in kinds
    assert ("claim:C1", "measured_at", "version:abc") in kinds


def test_traversal_answers_why_do_you_claim_x():
    g = build_graph(_nodes())
    support = [e.dst for e in g.out("claim:C1", kind="supported_by")]
    assert support == ["artifact:data/a.txt"]
    assert g.node("artifact:data/a.txt").attrs["exists"] is True


def test_by_kind_is_sorted_for_determinism():
    g = build_graph(_nodes())
    assert [n.id for n in g.by_kind("claim")] == ["claim:C1"]
    assert g.node("missing") is None
