"""RC1–RC9 — deterministic functions of (declarations × repository state).

Reserved role names (schema v1 law): `code` scopes RC5's import scan and
`adr` scopes RC6 — scope lives in the Constitution's role declarations,
not in hardcoded paths. RC2 reference resolution order (architecture §6):
the referencing file's directory, then the repo root, then each declared
frozen (evaluation-consumer) root. Findings are advisory: Law 10's two
legal exits are fixing the repository or amending the Constitution with
justification — never weakening a check.
"""
from __future__ import annotations

import ast
import contextlib
import json
import re
import sys
from pathlib import Path

from .inventory import match_role
from .loader import git_diff_names, git_object_exists
from .model import Finding, RepoDeclarations

_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_TICK = re.compile(r"`([^`]+)`")
_SHA = re.compile(r"[0-9a-f]{7,40}\Z")
_TRIGGER = re.compile(r"^## Review trigger", re.M)


def _rc1(index: tuple[str, ...], decls: RepoDeclarations) -> list[Finding]:
    return [
        Finding("RC1", path, "no role rule matches this tracked path")
        for path in index
        if match_role(path, decls.roles) is None
    ]


def _reference_resolves(root: Path, referencing: str, target: str, frozen_roots: list[str]) -> bool:
    bases = [Path(referencing).parent.as_posix(), ".", *frozen_roots]
    return any((root / base / target).exists() for base in bases)


def _rc2(root: Path, decls: RepoDeclarations, index: tuple[str, ...]) -> list[Finding]:
    out = []
    frozen_roots = [f["path"] for f in decls.frozen]
    for path in index:
        rule = match_role(path, decls.roles)
        if rule is None or rule["lifecycle"] != "living" or not path.endswith(".md"):
            continue
        for lineno, line in enumerate((root / path).read_text().splitlines(), 1):
            candidates = []
            for m in _LINK.finditer(line):
                target = m.group(1).split("#", 1)[0].strip()
                if target and "://" not in target and not target.startswith("mailto:"):
                    candidates.append(target)
            for m in _TICK.finditer(line):
                cand = m.group(1)
                if any(c in cand for c in "*?…{}<> \t"):
                    continue  # patterns/templates/commands, not concrete paths
                if match_role(cand, decls.roles) is not None:
                    candidates.append(cand)
            for target in candidates:
                if not _reference_resolves(root, path, target, frozen_roots):
                    out.append(
                        Finding("RC2", path, f"unresolved reference: {target}", lineno)
                    )
    return out


def _versions_agree(a: str, b: str) -> bool:
    return a == b or a.startswith(b + ".") or b.startswith(a + ".")


def _rc3(root: Path, decls: RepoDeclarations) -> list[Finding]:
    out, values = [], []
    for anchor in decls.version_anchors:
        p = root / anchor["file"]
        if not p.exists():
            out.append(Finding("RC3", anchor["file"], "version-anchor file missing"))
            continue
        m = re.search(anchor["pattern"], p.read_text(), re.M)
        if m is None:
            out.append(
                Finding("RC3", anchor["file"], "version-anchor pattern matched nothing")
            )
        else:
            values.append((anchor["file"], m.group(1)))
    if values:
        ref_file, ref = values[0]
        out += [
            Finding("RC3", f, f"version {v} disagrees with {ref_file} ({ref})")
            for f, v in values[1:]
            if not _versions_agree(v, ref)
        ]
    return out


def _rc4(decls: RepoDeclarations, index: tuple[str, ...]) -> list[Finding]:
    out = []
    for d in decls.derived_artifacts:
        if not str(d.get("regen", "")).strip():
            out.append(
                Finding("RC4", d["path"], "derived artifact declares no regeneration command")
            )
        elif d["path"] not in index:
            out.append(Finding("RC4", d["path"], "declared derived artifact is not tracked"))
    return out


def _under(mod: str, prefix: str) -> bool:
    return mod == prefix or mod.startswith(prefix + ".")


def _imports_of(root: Path, mod: str, path: str) -> list[tuple[str, int]]:
    tree = ast.parse((root / path).read_text(), filename=path)
    pkg = mod.split(".") if path.endswith("__init__.py") else mod.split(".")[:-1]
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(alias.name, node.lineno) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                found.append((node.module, node.lineno))
            elif node.level:
                base = pkg[: len(pkg) - (node.level - 1)]
                target = ".".join(base + ([node.module] if node.module else []))
                if target:
                    found.append((target, node.lineno))
    return found


def _rc5(root: Path, decls: RepoDeclarations, index: tuple[str, ...]) -> list[Finding]:
    mods: dict[str, str] = {}
    for path in index:
        rule = match_role(path, decls.roles)
        if path.endswith(".py") and rule is not None and rule["role"] == "code":
            mod = path[: -len(".py")].replace("/", ".")
            mod = mod[: -len(".__init__")] if mod.endswith(".__init__") else mod
            mods[mod] = path
    out = []
    for mod in sorted(mods):
        path = mods[mod]
        for target, lineno in _imports_of(root, mod, path):
            for rule in decls.layer_rules:
                kind = rule["kind"]
                if kind == "forbid" and _under(mod, rule["src"]) and _under(target, rule["dst"]):
                    out.append(Finding(
                        "RC5", path,
                        f"forbidden import {mod} -> {target} ({rule['src']} must not import {rule['dst']})",
                        lineno,
                    ))
                elif kind == "stdlib_only" and _under(mod, rule["src"]):
                    if not _under(target, rule["src"]) and target.split(".")[0] not in sys.stdlib_module_names:
                        out.append(Finding(
                            "RC5", path,
                            f"non-stdlib import in {rule['src']}: {mod} -> {target}",
                            lineno,
                        ))
                elif kind == "only_importer" and _under(target, rule["dst"]) and not _under(mod, rule["dst"]):  # noqa: SIM102
                    if not any(_under(mod, a) for a in rule["allowed"]):
                        out.append(Finding(
                            "RC5", path,
                            f"only {sorted(rule['allowed'])} may import {rule['dst']}: {mod} -> {target}",
                            lineno,
                        ))
    return out


def _rc6(root: Path, decls: RepoDeclarations, index: tuple[str, ...]) -> list[Finding]:
    return [
        Finding("RC6", path, "accepted ADR carries no '## Review trigger' section")
        for path in index
        if (rule := match_role(path, decls.roles)) is not None
        and rule["role"] == "adr"
        and not _TRIGGER.search((root / path).read_text())
    ]


def _rc7(root: Path, debt: tuple, index: tuple[str, ...]) -> list[Finding]:
    out, seen, register = [], set(), "docs/debt.yaml"
    tracked = set(index)
    for item in debt:
        tag = f"debt #{item['id']}"
        if item["id"] in seen:
            out.append(Finding("RC7", register, f"{tag}: duplicate id"))
        seen.add(item["id"])
        if item["state"] in ("open", "accepted") and not item["evidence"]:
            out.append(Finding("RC7", register, f"{tag}: {item['state']} item cites no evidence path"))
        out += [
            Finding("RC7", register, f"{tag}: evidence path not tracked: {e}")
            for e in item["evidence"]
            if e not in tracked
        ]
        if item["state"] == "resolved":
            ref = str(item["resolution"]).strip()
            if not ref:
                out.append(Finding("RC7", register, f"{tag}: resolved without a resolution reference"))
            elif ref not in tracked and not (_SHA.match(ref) and git_object_exists(root, ref)):
                out.append(Finding("RC7", register, f"{tag}: resolution reference not found in git: {ref}"))
    return out


def _rc8(root: Path, decls: RepoDeclarations) -> list[Finding]:
    out = []
    for f in decls.frozen:
        if not git_object_exists(root, str(f["commit"])):
            out.append(Finding("RC8", f["path"], f"freeze commit not found: {f['commit']}"))
            continue
        out += [
            Finding("RC8", changed, f"frozen tree modified since {str(f['commit'])[:12]}")
            for changed in git_diff_names(root, str(f["commit"]), f["path"])
        ]
    return out


_FENCE = re.compile(r"^\s*```")
# A measured ratio in this project lies in [0, 1]: precision, recall, F1 and
# every rate. Restricting the grammar to that range is not a convenience, it
# is what makes the check precise — it structurally cannot see an arXiv id
# (2507.20526), a Python version (3.11) or any other identifier that happens
# to carry a decimal point, so those need no exception list.
_DECIMAL = re.compile(r"(?<![\w.])(0\.\d{2,}|1\.0+)(?![\w.])")
_TRIPLE = re.compile(r"(?<![\w/.])(\d+)\s*/\s*(\d+)\s*/\s*(\d+)(?![\w/.])")
_LABELLED_TRIPLE = re.compile(
    r"tp\s*(\d+)\s*/\s*fp\s*(\d+)\s*/\s*fn\s*(\d+)", re.I
)


def _register_numbers(root: Path, decls: RepoDeclarations, index: tuple[str, ...]) -> tuple[set[str], set[tuple[int, int, int]]]:
    """Every number a living document may quote: values declared in the claims
    register, and values inside tracked metric artifacts.

    The register is read by regex, not parsed: the steward is stdlib-only and
    the flow reader does not cover its nested block style, but this check needs
    only the SET of declared numbers. Over-accepting is the safe direction —
    Law 3 retires a check on sustained false positives, so one that
    occasionally lets a stale number pass survives and one that cries wolf
    does not."""
    decimals: set[str] = set()
    triples: set[tuple[int, int, int]] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if all(k in node for k in ("tp", "fp", "fn")):
                with contextlib.suppress(TypeError, ValueError):
                    triples.add((int(node["tp"]), int(node["fp"]), int(node["fn"])))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            decimals.add(repr(float(node)))

    for path in index:
        rule = match_role(path, decls.roles)
        if rule is None:
            continue
        full = root / path
        if not full.exists():
            continue
        if path.endswith(".json"):
            try:
                walk(json.loads(full.read_text()))
            except (json.JSONDecodeError, OSError):
                continue
        elif rule.get("role") == "register":
            for m in _DECIMAL.finditer(full.read_text()):
                decimals.add(repr(float(m.group(1))))
    return decimals, triples


def _resolves(literal: str, decimals: set[str]) -> bool:
    """Resolves if a declared value rounds to it at the precision the document
    chose: prose saying 0.89 for a measured 0.8936 rounded, it did not drift."""
    places = len(literal.split(".", 1)[1])
    target = float(literal)
    return any(round(float(v), places) == target for v in decimals)


def _law_path(decls: RepoDeclarations, index: tuple[str, ...]) -> str:
    for path in index:
        rule = match_role(path, decls.roles)
        if rule is not None and rule.get("role") == "law":
            return path
    return "docs/CONSTITUTION.md"


def _rc9(root: Path, decls: RepoDeclarations, index: tuple[str, ...]) -> list[Finding]:
    """Numeric claims in living documents resolve to a declared register value.

    RC2 checks that a living document's *links* resolve. Nothing checked that
    its *prose* agrees, so the drift class the meta-engine exists to kill — a
    documented number the artifact no longer produces — stayed live outside the
    eleven figures CT5 covers.

    Grammar is narrow by construction, not by exception list: ratios in [0, 1]
    with two or more places, and confusion triples (labelled anywhere, bare only
    in a table cell). Integers never match, so counts, line numbers, indices and
    dates cannot fire; identifiers carrying a decimal point (an arXiv id, a
    Python version) fall outside [0, 1]. Fenced blocks and inline backticks are
    stripped — code and command output are not claims.

    Historical documents are exempt, by the same lifecycle law that exempts them
    from RC2: a shipped record correctly states the number it shipped with, and
    rewriting it to match today's artifact would falsify the record."""
    out: list[Finding] = []
    law = _law_path(decls, index)
    allowed: set[str] = set()
    for entry in decls.numeric_allowlist:
        # The entry still covers its literal even when it is malformed: an
        # exemption suppresses visibly, never silently, so the reported defect
        # is the missing justification rather than the drift underneath it.
        # Dropping coverage here would report two findings for one cause and
        # bury the actionable one.
        allowed.add(f"{entry.get('path')}::{entry.get('literal')}")
        if not str(entry.get("reason", "")).strip():
            out.append(
                Finding(
                    "RC9",
                    law,
                    f"numeric_allowlist entry {entry.get('literal')!r} carries no "
                    f"reason; an unexplained exemption is itself a finding",
                )
            )

    decimals, triples = _register_numbers(root, decls, index)

    for path in index:
        rule = match_role(path, decls.roles)
        if rule is None or rule["lifecycle"] != "living" or not path.endswith(".md"):
            continue
        fenced = False
        for lineno, line in enumerate((root / path).read_text().splitlines(), 1):
            if _FENCE.match(line):
                fenced = not fenced
                continue
            if fenced:
                continue
            bare = _TICK.sub(" ", line)
            for m in _LABELLED_TRIPLE.finditer(bare):
                trip = tuple(int(g) for g in m.groups())
                if trip not in triples and f"{path}::{m.group(0)}" not in allowed:
                    out.append(
                        Finding("RC9", path, f"unregistered counts: {m.group(0)}", lineno)
                    )
            # A bare a/b/c is only read as a confusion triple inside a table
            # cell, where a metric table puts it. In prose the same shape is a
            # step budget (6/12/24) or an exit-code set (0/1/2), and reading
            # those as counts is how a check earns a reputation for crying wolf.
            for m in (_TRIPLE.finditer(_LABELLED_TRIPLE.sub(" ", bare))
                      if bare.lstrip().startswith("|") else ()):
                trip = tuple(int(g) for g in m.groups())
                if trip not in triples and f"{path}::{m.group(0)}" not in allowed:
                    out.append(
                        Finding("RC9", path, f"unregistered counts: {m.group(0)}", lineno)
                    )
            for m in _DECIMAL.finditer(bare):
                lit = m.group(1)
                if not _resolves(lit, decimals) and f"{path}::{lit}" not in allowed:
                    out.append(
                        Finding(
                            "RC9",
                            path,
                            f"numeric claim {lit} resolves to no declared register value",
                            lineno,
                        )
                    )
    return out


def run_checks(
    root: Path, decls: RepoDeclarations, debt: tuple[dict[str, object], ...], index: tuple[str, ...]
) -> tuple[tuple[Finding, ...], tuple[Finding, ...]]:
    """All contracts; returns (active, exempted), each sorted. Exemptions
    suppress visibly — the finding moves to the exempted list, never
    disappears (R3 instrument reports count + age)."""
    findings = sorted(
        _rc1(index, decls)
        + _rc2(root, decls, index)
        + _rc3(root, decls)
        + _rc4(decls, index)
        + _rc5(root, decls, index)
        + _rc6(root, decls, index)
        + _rc7(root, debt, index)
        + _rc8(root, decls)
        + _rc9(root, decls, index),
        key=Finding.sort_key,
    )
    exempt = {(e["check"], e["path"]) for e in decls.exemptions}
    active = tuple(f for f in findings if (f.check_id, f.path) not in exempt)
    exempted = tuple(f for f in findings if (f.check_id, f.path) in exempt)
    return active, exempted
