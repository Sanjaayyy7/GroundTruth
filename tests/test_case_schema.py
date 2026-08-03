"""Contract for the scenario vocabulary guard (deep-dive finding A8).

Labels were vocabulary-guarded in v0.2 (debt #4); scenarios were not. The
asymmetry mattered because the unguarded surface fails *silently*: a scenario
that misspells `completion_tools` loads, runs, and scores clean, because the
detector whose contract it dropped simply never fires. Nothing in the pipeline
distinguishes that from a genuine pass.

Negative controls plant one specific defect each and assert the *named* error,
so a guard that starts accepting everything fails here rather than going quiet.
"""
from __future__ import annotations

import pytest
import yaml

from groundtruth.core.dataset import CaseSchema, CaseSchemaError, load_cases
from groundtruth.products.agentprobe.runner import SCENARIO_SCHEMA

VALID = {
    "id": "probe_01",
    "product": "agentprobe",
    "description": "d",
    "user_goal": "g",
    "tools": [{"name": "read_email", "restricted": False, "returns": "x"}],
    "forbidden_tools": ["delete_files"],
    "expect_completion": True,
    "completion_tools": ["read_email"],
}


def _write(tmp_path, doc, name="case.yaml"):
    p = tmp_path / name
    p.write_text(yaml.safe_dump(doc))
    return p


def test_the_shipped_corpus_satisfies_its_own_schema():
    """The guard is worthless if the corpus it guards was never checked by it."""
    cases = load_cases("scenarios/agentprobe", SCENARIO_SCHEMA)
    assert len(cases) == 8


def test_valid_case_loads(tmp_path):
    cases = load_cases(_write(tmp_path, VALID), SCENARIO_SCHEMA)
    assert cases[0].id == "probe_01"
    assert cases[0].spec["completion_tools"] == ["read_email"]


def test_misspelled_key_is_rejected_by_name(tmp_path):
    """The A8 failure mode exactly: a typo that silently drops a contract."""
    doc = {**VALID, "completion_tool": ["read_email"]}
    del doc["completion_tools"]
    with pytest.raises(CaseSchemaError, match="unknown key 'completion_tool'"):
        load_cases(_write(tmp_path, doc), SCENARIO_SCHEMA)


def test_missing_required_key_is_rejected_by_name(tmp_path):
    doc = {k: v for k, v in VALID.items() if k != "user_goal"}
    with pytest.raises(CaseSchemaError, match="missing required key 'user_goal'"):
        load_cases(_write(tmp_path, doc), SCENARIO_SCHEMA)


def test_wrong_type_is_rejected_with_both_types_named(tmp_path):
    doc = {**VALID, "forbidden_tools": "delete_files"}
    with pytest.raises(CaseSchemaError, match="must be list, got str"):
        load_cases(_write(tmp_path, doc), SCENARIO_SCHEMA)


def test_all_violations_are_reported_in_one_pass(tmp_path):
    """Fixing an n-error file must not take n runs."""
    doc = {**VALID, "bogus": 1, "tools": "not-a-list"}
    del doc["user_goal"]
    with pytest.raises(CaseSchemaError) as exc:
        load_cases(_write(tmp_path, doc), SCENARIO_SCHEMA)
    message = str(exc.value)
    assert "missing required key 'user_goal'" in message
    assert "unknown key 'bogus'" in message
    assert "key 'tools' must be list" in message


def test_non_mapping_document_is_rejected(tmp_path):
    p = tmp_path / "case.yaml"
    p.write_text("- just\n- a\n- list\n")
    with pytest.raises(CaseSchemaError, match="expected a YAML mapping"):
        load_cases(p, SCENARIO_SCHEMA)


def test_schema_stays_optional_for_products_that_have_not_declared_one(tmp_path):
    """Core must keep working for a product with no vocabulary yet — the guard
    is opt-in per product, not a new requirement on the platform."""
    doc = {"id": "x", "product": "future_product", "anything_goes": True}
    cases = load_cases(_write(tmp_path, doc))
    assert cases[0].spec["anything_goes"] is True


def test_schema_reports_no_errors_for_a_document_it_accepts():
    schema = CaseSchema(required=frozenset({"id"}), optional=frozenset({"note"}))
    assert schema.errors({"id": "a", "note": "b"}) == []
