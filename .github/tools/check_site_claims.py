"""Assert every number a rendered page states is one the claims register supports.

The marketing site lives in a separate repository. It is not under the
Constitution, not steward-checked, not in CI, and has no claims register — so
the public face of a project whose thesis is "documented numbers must match
their artifacts" is the one surface exempt from that rule. This closes it from
the side that owns the evidence: the register ships the checker, the site runs
it, and a page that quotes an unsupported number fails its own build.

The page is already 80% instrumented. Each stat carries
`title="Source: git rev-list --count HEAD @ <sha> (verified <date>)"`, so the
provenance is written down and simply never verified. A stat with no title is
reported as its own class, because an uncited number is worse than a stale one.

Stdlib only, so the site repo needs no install step and no Python packaging.
The register is read by regex rather than parsed for the same reason and with
the same tradeoff RC9 documents: this needs the SET of supported numbers, never
their structure, and over-accepting is the safe direction for a check whose
retirement condition is a sustained false-positive rate.

Usage in the site repository's CI:

    - name: Rendered stats must appear in the claims register
      run: |
        curl -sfo claims.yaml \\
          https://raw.githubusercontent.com/Sanjaayyy7/GroundTruth/main/docs/claims.yaml
        python check_site_claims.py --html out/index.html --claims claims.yaml

Exit codes: 0 every stat resolves · 1 findings · 2 usage or read error.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

#: Ratios in [0, 1] with two or more places, and integers of three digits or
#: fewer. Same grammar RC9 settled on after a wider one reported an arXiv id and
#: a Python version: identifiers carrying a decimal point fall outside [0, 1],
#: and a four-digit integer is a year or a line count, not a published metric.
_NUM = re.compile(r"(?<![\w.])(0\.\d{2,}|1\.0+|\d{1,3})(?![\w.%])")
_SOURCE = re.compile(r"Source:\s*(.+?)\s*$")

#: HTML void elements: they emit a start tag and never an end tag.
_VOID = frozenset(
    {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }
)


class StatExtractor(HTMLParser):
    """Collects <dd> text and its title attribute — the shape the site uses.

    `aria-hidden="true"` subtrees are skipped, and the reason is a finding this
    check produced against the live site. An accessible animated counter renders
    its value twice — once in a screen-reader span, once in an `aria-hidden`
    span that the animation drives — so naive concatenation reads a milestone
    count of 9 as the number "99", and reported it as an unsupported stat. No
    user ever saw "99": a screen reader reads the first span, a sighted reader
    sees the second. The stat was an artifact of the extractor, not of the page.

    This is the same correction RC9 made after a wider grammar reported an arXiv
    id: when a check fires on something no reader can observe, the check is
    wrong. Skipping the hidden copy also keeps the extractor honest in the other
    direction — a number rendered *only* inside `aria-hidden` is invisible to
    assistive tech and should not silently count as published.
    """

    def __init__(self) -> None:
        super().__init__()
        self.stats: list[tuple[str, str | None]] = []
        self._depth = 0
        self._title: str | None = None
        self._buf: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        pairs = dict(attrs)
        if self._hidden_depth or pairs.get("aria-hidden") == "true":
            # Track nesting so the skip ends at the matching close tag, not at
            # the first close tag of any descendant. Void elements never emit an
            # end tag, so counting them would strand the skip open for the rest
            # of the document and silently drop every later stat.
            if tag not in _VOID:
                self._hidden_depth += 1
            return
        if tag == "dd":
            self._depth += 1
            if self._depth == 1:
                self._title = pairs.get("title")
                self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if self._hidden_depth:
            self._hidden_depth -= 1
            return
        if tag == "dd" and self._depth:
            self._depth -= 1
            if self._depth == 0:
                text = " ".join("".join(self._buf).split())
                if text:
                    self.stats.append((text, self._title))

    def handle_data(self, data: str) -> None:
        if self._depth and not self._hidden_depth:
            self._buf.append(data)


def register_numbers(claims: str) -> set[str]:
    """Every number the register supports, normalised for comparison."""
    return {_norm(m.group(1)) for m in _NUM.finditer(claims)}


def _norm(literal: str) -> str:
    return repr(float(literal))


def resolves(literal: str, supported: set[str]) -> bool:
    """A quoted figure resolves if a supported value rounds to it at the
    precision the page chose: a page saying 0.95 for a measured 0.9545 rounded,
    it did not drift."""
    places = len(literal.split(".", 1)[1]) if "." in literal else 0
    target = float(literal)
    return any(round(float(v), places) == target for v in supported)


def check(html: str, claims: str) -> list[str]:
    parser = StatExtractor()
    parser.feed(html)
    supported = register_numbers(claims)
    findings: list[str] = []
    for text, title in parser.stats:
        literals = [m.group(1) for m in _NUM.finditer(text)]
        if not literals:
            continue
        if not title or not _SOURCE.search(title):
            findings.append(f"uncited stat (no Source: title): {text!r}")
            continue
        for literal in literals:
            if not resolves(literal, supported):
                findings.append(f"{literal} in {text!r} is in no claim in the register")
    return findings


def _read(location: str) -> str:
    if location.startswith(("http://", "https://")):
        with urllib.request.urlopen(location, timeout=30) as resp:  # noqa: S310
            return resp.read().decode("utf-8", "replace")
    return Path(location).read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="check_site_claims", description=__doc__)
    ap.add_argument("--html", required=True, help="rendered page: path or URL")
    ap.add_argument("--claims", required=True, help="claims.yaml: path or URL")
    args = ap.parse_args(argv)
    try:
        findings = check(_read(args.html), _read(args.claims))
    except OSError as exc:
        print(f"[site-claims] cannot read input: {exc}", file=sys.stderr)
        return 2
    if findings:
        print(f"[site-claims] {len(findings)} unsupported stat(s):", file=sys.stderr)
        for f in findings:
            print(f"  x {f}", file=sys.stderr)
        return 1
    print("[site-claims] every rendered stat resolves to the claims register")
    return 0


if __name__ == "__main__":
    sys.exit(main())
