"""Evidence Model — typed nodes, no I/O, hashable/frozen."""
import dataclasses

import pytest

from groundtruth.meta.model import KINDS, Edge, EvidenceNode, Provenance


def test_evidence_node_is_frozen_and_typed():
    node = EvidenceNode(
        id="claim:C1",
        kind="claim",
        provenance=Provenance(source="docs/claims.yaml", location="C1"),
        attrs={"classification": "fact"},
    )
    assert node.kind in KINDS
    with pytest.raises(dataclasses.FrozenInstanceError):
        node.id = "other"


def test_unknown_kind_rejected():
    with pytest.raises(ValueError, match="unknown kind"):
        EvidenceNode(id="x", kind="banana", provenance=Provenance(source="s"), attrs={})


def test_edge_is_plain_triple():
    e = Edge(src="claim:C1", kind="supported_by", dst="artifact:runs/detector-quality.json")
    assert (e.src, e.kind, e.dst) == ("claim:C1", "supported_by", "artifact:runs/detector-quality.json")
