"""Groundtruth Core — static HTML report.

Renders scorecards plus the detector-quality report into one self-contained
HTML file (ADR-0005: an evidence surface, not a dashboard). No JavaScript, no
external resources. Every value that originates in a trace is escaped: traces
carry adversarial content by design, so an unescaped report would execute the
very injections AgentProbe exists to catch.

Deterministic: identical inputs produce identical bytes (subjects are sorted,
no timestamps), so reports can be diffed and committed as artifacts.
"""
from __future__ import annotations

import html
from typing import Any

from .scorecard import SEVERITIES

_e = html.escape

_CSS = """
body { font-family: -apple-system, 'Segoe UI', sans-serif; margin: 2rem auto;
       max-width: 60rem; padding: 0 1rem; color: #1a1d21; background: #fff; }
h1 { font-size: 1.4rem; } h2 { font-size: 1.1rem; margin-top: 2rem; }
table { border-collapse: collapse; width: 100%; margin: .75rem 0; }
th, td { border: 1px solid #d5d9de; padding: .35rem .6rem; text-align: left;
         font-size: .85rem; vertical-align: top; }
th { background: #f2f4f6; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
td.fail { color: #b3261e; font-weight: 600; text-align: center; }
td.pass { color: #9aa1a9; text-align: center; }
.failure { border: 1px solid #d5d9de; border-left: 4px solid #b3261e;
           padding: .5rem .8rem; margin: .6rem 0; font-size: .85rem; }
.failure .meta { color: #5f6670; }
.muted { color: #5f6670; font-size: .8rem; }
code { background: #f2f4f6; padding: 0 .25rem; font-size: .85em; }
"""


def render_html(scorecards: list[dict[str, Any]], quality: dict[str, Any] | None = None) -> str:
    cards = sorted(scorecards, key=lambda c: c["subject"])
    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<title>Groundtruth report</title>",
        f"<style>{_CSS}</style></head><body>",
        "<h1>Groundtruth &middot; evaluation report</h1>",
        "<p class='muted'>Static evidence artifact. Deterministic render of "
        "persisted scorecards and the measured detector-quality report.</p>",
        _subjects_table(cards),
        _case_matrix(cards),
        _failure_details(cards),
    ]
    if quality:
        parts.append(_quality_section(quality))
    parts.append("</body></html>")
    return "".join(p for p in parts if p)


def _subjects_table(cards: list[dict[str, Any]]) -> str:
    rows = []
    for c in cards:
        sev = ", ".join(
            f"{s}={c['by_severity'][s]}" for s in SEVERITIES if s in c.get("by_severity", {})
        )
        cats = ", ".join(f"{k}&times;{v}" for k, v in sorted(c.get("by_category", {}).items()))
        rows.append(
            f"<tr><td><code>{_e(c['subject'])}</code></td>"
            f"<td class='num'>{c['robustness_score']}</td>"
            f"<td class='num'>{c['n_cases']}</td>"
            f"<td class='num'>{c['n_failures']}</td>"
            f"<td>{_e(sev, quote=False)}</td><td>{cats}</td></tr>"
        )
    return (
        "<h2>Subjects compared</h2>"
        "<table><tr><th>subject</th><th>robustness</th><th>cases</th>"
        "<th>failures</th><th>by severity</th><th>by category</th></tr>"
        + "".join(rows) + "</table>"
    )


def _case_matrix(cards: list[dict[str, Any]]) -> str:
    failed_by_subject = {c["subject"]: {f["case_id"] for f in c["failures"]} for c in cards}
    all_cases = sorted(set().union(*failed_by_subject.values())) if failed_by_subject else []
    if not all_cases:
        return ""
    head = "".join(f"<th>{_e(cid)}</th>" for cid in all_cases)
    rows = []
    for c in cards:
        cells = "".join(
            "<td class='fail'>&#10007;</td>" if cid in failed_by_subject[c["subject"]]
            else "<td class='pass'>&middot;</td>"
            for cid in all_cases
        )
        rows.append(f"<tr><td><code>{_e(c['subject'])}</code></td>{cells}</tr>")
    return (
        "<h2>Failing-case matrix</h2>"
        "<p class='muted'>Only cases failed by at least one subject are shown.</p>"
        f"<table><tr><th>subject</th>{head}</tr>" + "".join(rows) + "</table>"
    )


def _failure_details(cards: list[dict[str, Any]]) -> str:
    blocks = []
    for c in cards:
        if not c["failures"]:
            continue
        blocks.append(f"<h2>Failures &middot; <code>{_e(c['subject'])}</code></h2>")
        for f in c["failures"]:
            chain = "".join(f"<li>{_e(step)}</li>" for step in f.get("chain", []))
            blocks.append(
                "<div class='failure'>"
                f"<div class='meta'>[{_e(f['severity'])}] <code>{_e(f['case_id'])}</code>"
                f" &middot; {_e(f['category'])} ({_e(f['detector'])})</div>"
                f"<div>{_e(f['summary'])}</div>"
                f"<ul>{chain}</ul>"
                f"<div><strong>fix:</strong> {_e(f.get('recommendation', ''))}</div>"
                "</div>"
            )
    return "".join(blocks)


def _quality_section(q: dict[str, Any]) -> str:
    m = q["micro"]
    rows = []
    for cat, v in sorted(q.get("per_category", {}).items()):
        misses = "".join(
            f"<div class='muted'>missed: <code>{_e(i)}</code></div>" for i in v.get("fn_ids", [])
        ) + "".join(
            f"<div class='muted'>wrongly flagged: <code>{_e(i)}</code></div>"
            for i in v.get("fp_ids", [])
        )
        rows.append(
            f"<tr><td>{_e(cat)}</td><td class='num'>{v['precision']}</td>"
            f"<td class='num'>{v['recall']}</td><td class='num'>{v['f1']}</td>"
            f"<td class='num'>{v['tp']}/{v['fp']}/{v['fn']}</td><td>{misses}</td></tr>"
        )
    return (
        "<h2>Detector quality (measured)</h2>"
        f"<p>Labeled items: {q['n_items']} &middot; "
        f"micro precision <strong>{m['precision']}</strong>, "
        f"recall <strong>{m['recall']}</strong>, f1 <strong>{m['f1']}</strong> "
        f"<span class='muted'>(tp {m['tp']} / fp {m['fp']} / fn {m['fn']})</span></p>"
        "<table><tr><th>category</th><th>precision</th><th>recall</th><th>f1</th>"
        "<th>tp/fp/fn</th><th>audit trail</th></tr>"
        + "".join(rows) + "</table>"
        "<p class='muted'>Misses are published deliberately: detector quality is a "
        "measured claim, not an assumption.</p>"
    )
