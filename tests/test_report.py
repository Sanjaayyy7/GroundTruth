"""`groundtruth report` — deterministic, self-contained HTML from runs/ artifacts.

The report is an evidence surface, not a dashboard (ADR-0005): comparative
robustness across subjects, the failing-case matrix, explanatory failures, and
the detector-quality section with misses published. Traces carry adversarial
content by design, so escaping is a correctness requirement, not hygiene.
"""
from __future__ import annotations

import json

from groundtruth.cli import main
from groundtruth.core.report import render_html


def _failure(case_id="indirect_injection_02", summary="agent obeyed injected instruction"):
    return {
        "case_id": case_id,
        "detector": "injection_compliance",
        "category": "instruction_hijacking",
        "severity": "critical",
        "summary": summary,
        "chain": ["'search_web' output carried an injected instruction"],
        "recommendation": "treat retrieved content as untrusted data",
    }


def _card(subject, robustness=1.0, failures=()):
    failures = list(failures)
    return {
        "schema_version": 1,
        "subject": subject,
        "suite": "agentprobe",
        "n_cases": 8,
        "robustness_score": robustness,
        "n_failures": len(failures),
        "by_severity": {"critical": len(failures)} if failures else {},
        "by_category": {f["category"]: 1 for f in failures},
        "failures": failures,
    }


def test_report_compares_all_subjects_with_failing_case_matrix():
    html = render_html(
        [
            _card("ollama:gemma3:4b", 0.875, [_failure()]),
            _card("hardened_agent", 1.0),
        ]
    )

    assert "ollama:gemma3:4b" in html
    assert "hardened_agent" in html
    assert "0.875" in html
    # the failing case is named so models can be compared per scenario
    assert "indirect_injection_02" in html
    # explanatory failure detail survives into the report — the differentiator
    assert "treat retrieved content as untrusted data" in html


def test_adversarial_trace_content_is_escaped():
    payload = "<script>alert('pwned')</script>"
    html = render_html([_card("v", 0.5, [_failure(summary=payload)])])

    assert payload not in html
    assert "&lt;script&gt;" in html


def test_output_is_deterministic_and_input_order_independent():
    a, b = _card("subject_a", 1.0), _card("subject_b", 0.75, [_failure()])

    assert render_html([a, b]) == render_html([b, a])


def test_detector_quality_section_publishes_misses():
    quality = {
        "schema_version": 1,
        "n_items": 53,
        "micro": {"tp": 28, "fp": 3, "fn": 5, "precision": 0.9032, "recall": 0.8485, "f1": 0.875},
        "per_category": {
            "unsafe_tool_invocation": {
                "tp": 4, "fp": 0, "fn": 1,
                "precision": 1.0, "recall": 0.8, "f1": 0.8889,
                "fp_ids": [], "fn_ids": ["ut_pos_04_semantic_gap"],
            }
        },
    }

    html = render_html([_card("v")], quality=quality)

    assert "0.9032" in html
    assert "ut_pos_04_semantic_gap" in html  # misses are shown, not hidden


def test_report_is_self_contained():
    html = render_html([_card("v", 0.5, [_failure()])])

    for marker in ('src="http', "src='http", 'href="http', "<link", "@import"):
        assert marker not in html


def test_report_command_builds_html_from_runs_dir(tmp_path):
    old_card = _card("ollama:gemma3:4b", 0.875, [_failure()])
    del old_card["schema_version"]  # pre-v0.3 artifact — must still render
    (tmp_path / "scorecard-gemma3-4b.json").write_text(json.dumps(old_card))
    (tmp_path / "scorecard-hardened.json").write_text(json.dumps(_card("hardened_agent")))
    (tmp_path / "detector-quality.json").write_text(
        json.dumps({"n_items": 53, "micro": {"tp": 28, "fp": 3, "fn": 5,
                    "precision": 0.9032, "recall": 0.8485, "f1": 0.875},
                    "per_category": {}})
    )
    out = tmp_path / "report.html"

    rc = main(["report", "--runs", str(tmp_path), "--out", str(out)])

    assert rc == 0
    html = out.read_text()
    assert "ollama:gemma3:4b" in html
    assert "hardened_agent" in html
    assert "0.9032" in html


def test_report_exits_2_when_no_scorecards(tmp_path, capsys):
    rc = main(["report", "--runs", str(tmp_path), "--out", str(tmp_path / "r.html")])

    assert rc == 2
