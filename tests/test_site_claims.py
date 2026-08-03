"""Site claims checker — the public face runs the register's own rule.

Zero network: every case is an in-memory HTML string. The site repository is
separate and ungoverned, so this tool is the only mechanism that can make a
rendered number answerable to the register that produced it.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "check_site_claims", REPO / ".github/tools/check_site_claims.py"
)
assert _spec and _spec.loader
site = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(site)

CLAIMS = """
claims:
  - id: C6
    metrics:
      - {name: micro_precision, value: 0.9545}
      - {name: micro_recall, value: 0.8936}
    corpus: 68
"""
TITLE = 'title="Source: git rev-list --count HEAD @ 86ae6c2 (verified 2026-07-18)"'


def _page(body: str) -> str:
    return f"<html><body><dl>{body}</dl></body></html>"


def test_a_supported_stat_resolves():
    html = _page(f"<dt>precision</dt><dd {TITLE}>0.9545</dd>")
    assert site.check(html, CLAIMS) == []


def test_a_rounded_stat_resolves_at_the_precision_the_page_chose():
    """0.95 for a measured 0.9545 is rounding, not drift."""
    html = _page(f"<dt>precision</dt><dd {TITLE}>0.95</dd>")
    assert site.check(html, CLAIMS) == []


def test_a_stat_the_register_does_not_support_is_a_finding():
    """The exact drift this exists to catch: the page keeps the old number."""
    html = _page(f"<dt>precision</dt><dd {TITLE}>0.9333</dd>")
    findings = site.check(html, CLAIMS)
    assert len(findings) == 1
    assert "0.9333" in findings[0]


def test_an_uncited_stat_is_its_own_finding_class():
    """An uncited number is worse than a stale one — it cannot even be checked."""
    html = _page("<dt>precision</dt><dd>0.9545</dd>")
    findings = site.check(html, CLAIMS)
    assert len(findings) == 1
    assert "uncited" in findings[0]


def test_prose_without_numbers_is_ignored():
    html = _page(f"<dt>status</dt><dd {TITLE}>shipping</dd>")
    assert site.check(html, CLAIMS) == []


def test_the_checker_runs_against_this_repository_s_own_register():
    """The register must parse and yield the figures it actually declares."""
    claims = (REPO / "docs/claims.yaml").read_text()
    supported = site.register_numbers(claims)
    assert site.resolves("0.9545", supported)
    assert not site.resolves("0.1234", supported)
