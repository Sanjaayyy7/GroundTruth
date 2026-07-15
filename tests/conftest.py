"""Shared fixtures for the meta-evaluation test suite."""
from groundtruth.meta.model import EvidenceNode, Provenance

P = Provenance(source="fixture")


def green_nodes():
    """A minimal evaluation whose every contract holds."""
    return [
        EvidenceNode("claim:C1", "claim", P, {
            "classification": "fact", "evidence_paths": ["data/a.txt"],
            "external_evidence": [], "threat_refs": ["T1"],
            "reproduce": "python scripts/run.py", "falsification": "counterexample",
            "confidence": "high", "scope": "fixture", "confounds_remaining": [],
            "metrics_resolved": [
                {"name": "p", "value": 0.5, "source": "data/m.json", "path": "p", "actual": 0.5}],
        }),
        EvidenceNode("experiment:C1", "experiment", P, {
            "command": "python scripts/run.py", "script_paths": {"scripts/run.py": True}}),
        EvidenceNode("threat:T1", "threat", P, {
            "category": "internal", "status": "resolved", "claim_refs": ["C1"],
            "mitigation": "documented", "remaining_risk": "little",
            "future_experiment": "more runs", "evidence_paths": ["data/a.txt"]}),
        EvidenceNode("artifact:data/a.txt", "artifact", P, {"exists": True}),
        EvidenceNode("artifact:data/m.json", "artifact", P, {"exists": True}),
        EvidenceNode("version:abc", "version", P, {
            "exists_in_git": True, "pyproject_version": "0.6.0", "readme_version": "0.6"}),
        EvidenceNode("artifact:docs/THREATS_TO_VALIDITY.md", "artifact", P, {
            "exists": True, "prose_threat_ids": ["T1"]}),
    ]
