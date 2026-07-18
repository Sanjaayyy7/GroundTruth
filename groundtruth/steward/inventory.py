"""Steward inventory — git index × role declarations -> repository manifest.

Pattern law (schema v1): `**` crosses directory separators, `*` does not,
`?` matches one non-separator character; rules are evaluated in declaration
order and the first match wins. The rule list is deliberately catch-none:
an unmatched path is recorded with role None and becomes an RC1 finding.
"""
from __future__ import annotations

import re
from functools import lru_cache


@lru_cache(maxsize=None)
def _pattern_regex(pattern: str) -> re.Pattern:
    out = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def match_role(path: str, roles: tuple) -> dict | None:
    for rule in roles:
        if _pattern_regex(rule["pattern"]).match(path):
            return rule
    return None


def build_inventory(index: tuple, roles: tuple, sizes: dict) -> dict:
    """sizes maps path -> byte size of the *index blob* (loader.git_blob_sizes);
    working-tree sizes are forbidden here — the manifest lists itself and
    stat-based sizes would deny the artifact a byte fixed point."""
    files = []
    totals: dict[str, dict[str, int]] = {}
    for path in sorted(index):
        rule = match_role(path, roles)
        role = rule["role"] if rule else None
        lifecycle = rule["lifecycle"] if rule else None
        size = int(sizes.get(path, 0))
        files.append({"path": path, "role": role, "lifecycle": lifecycle, "bytes": size})
        if role is not None:
            bucket = totals.setdefault(role, {"files": 0, "bytes": 0})
            bucket["files"] += 1
            bucket["bytes"] += size
    return {
        "manifest_schema": 1,
        "files": files,
        "roles": {role: totals[role] for role in sorted(totals)},
        "total": {"files": len(files), "bytes": sum(f["bytes"] for f in files)},
    }
