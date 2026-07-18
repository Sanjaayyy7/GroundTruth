"""RC1–RC8 — deterministic functions of (declarations × repository state).

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


def _rc1(index: tuple, decls: RepoDeclarations) -> list[Finding]:
    return [
        Finding("RC1", path, "no role rule matches this tracked path")
        for path in index
        if match_role(path, decls.roles) is None
    ]


def _reference_resolves(root: Path, referencing: str, target: str, frozen_roots) -> bool:
    bases = [Path(referencing).parent.as_posix(), "."] + list(frozen_roots)
    return any((root / base / target).exists() for base in bases)


def _rc2(root: Path, decls: RepoDeclarations, index: tuple) -> list[Finding]:
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


def _rc4(decls: RepoDeclarations, index: tuple) -> list[Finding]:
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


def _rc5(root: Path, decls: RepoDeclarations, index: tuple) -> list[Finding]:
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
                elif kind == "only_importer" and _under(target, rule["dst"]) and not _under(mod, rule["dst"]):
                    if not any(_under(mod, a) for a in rule["allowed"]):
                        out.append(Finding(
                            "RC5", path,
                            f"only {sorted(rule['allowed'])} may import {rule['dst']}: {mod} -> {target}",
                            lineno,
                        ))
    return out


def _rc6(root: Path, decls: RepoDeclarations, index: tuple) -> list[Finding]:
    return [
        Finding("RC6", path, "accepted ADR carries no '## Review trigger' section")
        for path in index
        if (rule := match_role(path, decls.roles)) is not None
        and rule["role"] == "adr"
        and not _TRIGGER.search((root / path).read_text())
    ]


def _rc7(root: Path, debt: tuple, index: tuple) -> list[Finding]:
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


def run_checks(
    root: Path, decls: RepoDeclarations, debt: tuple, index: tuple
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
        + _rc8(root, decls),
        key=Finding.sort_key,
    )
    exempt = {(e["check"], e["path"]) for e in decls.exemptions}
    active = tuple(f for f in findings if (f.check_id, f.path) not in exempt)
    exempted = tuple(f for f in findings if (f.check_id, f.path) in exempt)
    return active, exempted
