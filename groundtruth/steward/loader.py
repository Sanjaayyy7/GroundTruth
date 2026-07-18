"""Steward loader — Constitution declarations block + debt register + the
enumerated read-only git surface.

No YAML dependency: the steward is stdlib-only by law (RC5 checks that law
on the steward itself), so declarations are written in a versioned flow
subset (schema v1 format law, ADR-0007 D2 discipline) and read here.
Anything outside the subset is a DeclarationError (CLI exit 2), never a
guess.

Allowed git surface (architecture §4, exhaustive): ls-files, rev-parse,
cat-file, diff --name-only, log --format=%H -n1 -- <path>. Only the subset
actually consumed is implemented. Every invocation pins byte-determinism
(tribunal R2): `-c core.quotePath=false`, NUL-delimited output, LC_ALL=C.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .model import DeclarationError, RepoDeclarations

LIFECYCLES = ("living", "historical", "derived", "frozen")
DEBT_STATES = ("open", "resolved", "accepted")
_SCHEMA_KEYS = (
    "constitution_schema", "roles", "version_anchors", "derived_artifacts",
    "frozen", "layer_rules", "exemptions",
)
_ROLE_FIELDS = ("pattern", "role", "lifecycle")
_DEBT_FIELDS = ("id", "title", "category", "state", "origin", "evidence", "resolution")
_BLOCK = re.compile(r"^```yaml\n(.*?)^```", re.M | re.S)
_INT = re.compile(r"-?\d+$")


def _skip_ws(text: str, pos: int) -> int:
    while pos < len(text) and text[pos] in " \t":
        pos += 1
    return pos


def _parse_value(text: str, pos: int) -> tuple[object, int]:
    pos = _skip_ws(text, pos)
    if pos >= len(text):
        raise DeclarationError("unexpected end of flow value")
    ch = text[pos]
    if ch == "{":
        mapping: dict = {}
        pos = _skip_ws(text, pos + 1)
        if pos < len(text) and text[pos] == "}":
            return mapping, pos + 1
        while True:
            pos = _skip_ws(text, pos)
            colon = text.find(":", pos)
            if colon < 0:
                raise DeclarationError("flow mapping: missing ':'")
            key = text[pos:colon].strip()
            value, pos = _parse_value(text, colon + 1)
            mapping[key] = value
            pos = _skip_ws(text, pos)
            if pos >= len(text):
                raise DeclarationError("flow mapping: missing '}'")
            if text[pos] == ",":
                pos += 1
                continue
            if text[pos] == "}":
                return mapping, pos + 1
            raise DeclarationError(f"flow mapping: unexpected {text[pos]!r}")
    if ch == "[":
        items: list = []
        pos = _skip_ws(text, pos + 1)
        if pos < len(text) and text[pos] == "]":
            return items, pos + 1
        while True:
            value, pos = _parse_value(text, pos)
            items.append(value)
            pos = _skip_ws(text, pos)
            if pos >= len(text):
                raise DeclarationError("flow list: missing ']'")
            if text[pos] == ",":
                pos = _skip_ws(text, pos + 1)
                continue
            if text[pos] == "]":
                return items, pos + 1
            raise DeclarationError(f"flow list: unexpected {text[pos]!r}")
    if ch == '"':
        out: list[str] = []
        i = pos + 1
        while i < len(text):
            c = text[i]
            if c == "\\" and i + 1 < len(text) and text[i + 1] in '"\\':
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                return "".join(out), i + 1
            out.append(c)
            i += 1
        raise DeclarationError("unterminated string")
    end = pos
    while end < len(text) and text[end] not in ",}]\n":
        end += 1
    token = text[pos:end].strip()
    return (int(token) if _INT.match(token) else token), end


def parse_document(text: str) -> dict:
    """Line-oriented reader for the schema-v1 subset: 'key: scalar-or-flow',
    or 'key:' followed by '- <flow item>' lines. Comments and blanks skipped."""
    doc: dict = {}
    current: list | None = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current is None:
                raise DeclarationError(f"line {lineno}: list item outside a list")
            value, _ = _parse_value(stripped[2:], 0)
            current.append(value)
            continue
        if ":" not in stripped:
            raise DeclarationError(f"line {lineno}: expected 'key: value'")
        key, _, rest = stripped.partition(":")
        key, rest = key.strip(), rest.strip()
        if not rest:
            current = []
            doc[key] = current
            continue
        current = None
        value, _ = _parse_value(rest, 0)
        doc[key] = value
    return doc


def load_constitution(path: Path) -> RepoDeclarations:
    if not path.exists():
        raise DeclarationError(f"constitution not found: {path}")
    block = next(
        (m.group(1) for m in _BLOCK.finditer(path.read_text())
         if "constitution_schema" in m.group(1)),
        None,
    )
    if block is None:
        raise DeclarationError(
            f"{path.name}: no ```yaml declarations block with constitution_schema"
        )
    doc = parse_document(block)
    if sorted(doc) != sorted(_SCHEMA_KEYS):
        missing, extra = set(_SCHEMA_KEYS) - set(doc), set(doc) - set(_SCHEMA_KEYS)
        raise DeclarationError(
            f"{path.name}: declarations must carry exactly the schema v1 keys "
            f"(missing={sorted(missing)}, extra={sorted(extra)})"
        )
    if doc["constitution_schema"] != 1:
        raise DeclarationError(f"{path.name}: unsupported constitution_schema")
    for rule in doc["roles"]:
        if not isinstance(rule, dict) or sorted(rule) != sorted(_ROLE_FIELDS):
            raise DeclarationError(f"{path.name}: role rule needs exactly {_ROLE_FIELDS}")
        if rule["lifecycle"] not in LIFECYCLES:
            raise DeclarationError(
                f"{path.name}: lifecycle {rule['lifecycle']!r} not in {LIFECYCLES}"
            )
    return RepoDeclarations(
        schema=1,
        roles=tuple(doc["roles"]),
        version_anchors=tuple(doc["version_anchors"]),
        derived_artifacts=tuple(doc["derived_artifacts"]),
        frozen=tuple(doc["frozen"]),
        layer_rules=tuple(doc["layer_rules"]),
        exemptions=tuple(doc["exemptions"]),
    )


def load_debt(path: Path) -> tuple[dict, ...]:
    if not path.exists():
        raise DeclarationError(f"debt register not found: {path}")
    doc = parse_document(path.read_text())
    if doc.get("debt_schema") != 1 or not isinstance(doc.get("items"), list):
        raise DeclarationError(f"{path.name}: expected debt_schema 1 with an items list")
    for item in doc["items"]:
        if not isinstance(item, dict) or sorted(item) != sorted(_DEBT_FIELDS):
            raise DeclarationError(f"{path.name}: debt item needs exactly {_DEBT_FIELDS}")
        if item["state"] not in DEBT_STATES:
            raise DeclarationError(
                f"{path.name}: state {item['state']!r} not in {DEBT_STATES}"
            )
        if not isinstance(item["evidence"], list):
            raise DeclarationError(f"{path.name}: evidence must be a list of paths")
    return tuple(doc["items"])


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=root, capture_output=True, text=True,
        env=dict(os.environ, LC_ALL="C"),
    )


def git_index(root: Path) -> tuple[str, ...]:
    proc = _git(root, "ls-files", "-z")
    if proc.returncode != 0:
        raise DeclarationError(f"git ls-files failed: {proc.stderr.strip()}")
    return tuple(sorted(p for p in proc.stdout.split("\0") if p))


def git_diff_names(root: Path, commit: str, path: str) -> tuple[str, ...]:
    proc = _git(root, "diff", "--name-only", "-z", commit, "--", path)
    if proc.returncode != 0:
        raise DeclarationError(
            f"git diff failed for {path} @ {commit}: {proc.stderr.strip()}"
        )
    return tuple(sorted(p for p in proc.stdout.split("\0") if p))


def git_object_exists(root: Path, sha: str) -> bool:
    proc = _git(root, "cat-file", "-t", str(sha))
    return proc.returncode == 0 and proc.stdout.strip() == "commit"
